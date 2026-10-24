"""The committed workspace snapshot: a clone must get exactly the source database.

The strongest test here loads `backend/snapshot/workspace.sql` into an
empty schema and re-exports it: the two files must be identical. That
one comparison covers type round-tripping, foreign-key order, the
case_events self-reference and a deterministic writer at once -- every
earlier attempt at reproducing this database failed on one of those
only at import time, never on reading the code.
"""

from __future__ import annotations

import sqlite3

import pytest

import app.db as db_module
from app.config import get_settings
from app.db import Base
from app.workspace import (
    SNAPSHOT_DIR,
    TABLE_ORDER,
    DatabaseNotEmpty,
    _insert_lines,
    apply_snapshot,
    ensure_schema,
    snapshot_sql_path,
    validate,
)
from app.workspace.export import (
    PersonalDataFound,
    _scan_value,
    export,
    literal,
    redact,
    scan_tables,
)


@pytest.fixture
def workspace_env(tmp_path, monkeypatch):
    """An empty, schema-only database with its own storage folders."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "repairflow.db"))
    monkeypatch.setenv("DOCUMENTS_DIR", str(tmp_path / "documents"))
    monkeypatch.setenv("RECORDINGS_DIR", str(tmp_path / "recordings"))
    get_settings.cache_clear()
    db_module._engine = None
    db_module._session_factory = None
    ensure_schema()
    yield tmp_path
    get_settings.cache_clear()


def _committed_sql() -> str:
    return snapshot_sql_path().read_text(encoding="utf-8")


def test_snapshot_is_committed_and_holds_the_whole_workspace() -> None:
    tables = _insert_lines(_committed_sql())
    assert len(tables["repair_cases"]) == 99
    assert len(tables["properties"]) == 12
    assert len(tables["tenants"]) == 12
    assert len(tables["contractors"]) == 24
    assert set(tables) <= set(TABLE_ORDER)
    assert "jobs" not in tables, "the wake-up queue is runtime state, never content"


def test_every_table_but_jobs_is_captured() -> None:
    """A table added to the models is captured without anyone listing it."""
    assert set(TABLE_ORDER) == set(Base.metadata.tables) - {"jobs"}


def test_insert_order_matches_the_foreign_key_graph() -> None:
    """Regression carried from app.intake_fixture: `dependencies` was once
    hand-listed before `contractor_reports`, which it references, and the
    import died on FOREIGN KEY constraint failed."""
    position = {t: i for i, t in enumerate(TABLE_ORDER)}
    for table in TABLE_ORDER:
        for column in Base.metadata.tables[table].columns:
            for fk in column.foreign_keys:
                target = fk.column.table.name
                if target == table:
                    continue  # rows within one table: deferred to COMMIT instead
                assert position[target] < position[table], f"{table}.{column.name} -> {target}"

    in_file = list(_insert_lines(_committed_sql()))
    assert in_file == [t for t in TABLE_ORDER if t in in_file]


def test_snapshot_carries_no_personal_data() -> None:
    """The same scan the exporter runs, applied to what is actually committed."""
    assert _scan_value(_committed_sql()) == []


def test_a_real_tenant_number_is_written_as_its_seed_placeholder() -> None:
    from app.seed import DEMO_TENANT_ID

    real = {"id": DEMO_TENANT_ID, "phone_e164": "+447700900123", "display_name": "Jordan Hale"}
    assert redact("tenants", real)["phone_e164"] == "+441179460000"

    placeholder = {"id": DEMO_TENANT_ID, "phone_e164": "+441179460000"}
    assert redact("tenants", placeholder) is placeholder

    # Only tenants are redacted; anywhere else a real number is refused.
    elsewhere = {"id": "m1", "text": "call me on +447700900123"}
    assert redact("messages", elsewhere) is elsewhere
    assert scan_tables({"messages": [elsewhere]})

    # A tenant app.seed never created has no placeholder to fall back on.
    unknown = {"id": "not-a-seeded-tenant", "phone_e164": "+447700900123"}
    assert redact("tenants", unknown) is unknown
    assert scan_tables({"tenants": [unknown]})


@pytest.mark.parametrize(
    "value",
    ["", "it's", "a\r\nb\nc\rd", "\n", "ends with a break\n", "\r\nstarts with one", 0, -3, 1.25, None],
)
def test_literal_round_trips_through_sqlite_on_one_line(value) -> None:
    rendered = literal(value)
    assert "\n" not in rendered and "\r" not in rendered
    assert sqlite3.connect(":memory:").execute(f"SELECT {rendered}").fetchone()[0] == value


def test_loading_into_an_empty_database_reproduces_the_snapshot_exactly(workspace_env, tmp_path) -> None:
    result = apply_snapshot()
    expected = _committed_sql()
    assert result.rows == sum(len(v) for v in _insert_lines(expected).values())

    report = validate()
    assert report.passed, [c for c in report.checks if not c.passed]

    out = tmp_path / "re-export"
    export(snapshot_dir=out)
    assert (out / "workspace.sql").read_text(encoding="utf-8") == expected

    committed = sorted(p.relative_to(SNAPSHOT_DIR / "files") for p in (SNAPSHOT_DIR / "files").rglob("*") if p.is_file())
    exported = sorted(p.relative_to(out / "files") for p in (out / "files").rglob("*") if p.is_file())
    assert exported == committed
    for rel in committed:
        assert (out / "files" / rel).read_bytes() == (SNAPSHOT_DIR / "files" / rel).read_bytes()

    # Git must not have rewritten the documents' line endings: their bytes
    # have to match the size the database recorded for them.
    documents = get_settings().documents_dir
    rows = sqlite3.connect(get_settings().database_path).execute(
        "SELECT stored_name, size_bytes FROM documents"
    ).fetchall()
    assert rows
    for name, size in rows:
        assert (documents / name).stat().st_size == size, name


def test_apply_refuses_existing_data_and_replace_copies_it_aside(workspace_env) -> None:
    apply_snapshot()
    with pytest.raises(DatabaseNotEmpty):
        apply_snapshot()

    path = get_settings().database_path
    with sqlite3.connect(path) as connection:
        note_id = connection.execute("SELECT id FROM notes ORDER BY id LIMIT 1").fetchone()[0]
        connection.execute("UPDATE notes SET body = 'edited locally' WHERE id = ?", (note_id,))

    drift = {c.name: c for c in validate().checks}["database_matches_snapshot"]
    assert not drift.passed
    assert "1 snapshot row(s) absent or different, 1 database row(s) not in the snapshot" in drift.detail

    result = apply_snapshot(replace=True)
    assert validate().passed
    assert result.backup is not None and result.backup.is_file()
    kept = sqlite3.connect(result.backup).execute("SELECT body FROM notes WHERE id = ?", (note_id,)).fetchone()
    assert kept == ("edited locally",)


def test_export_refuses_to_write_personal_data(workspace_env, tmp_path) -> None:
    apply_snapshot()
    with sqlite3.connect(get_settings().database_path) as connection:
        connection.execute("UPDATE notes SET body = 'reach me at someone@example.com'")

    out = tmp_path / "refused"
    with pytest.raises(PersonalDataFound):
        export(snapshot_dir=out)
    assert not (out / "workspace.sql").exists()


def test_bootstrap_loads_an_empty_database_and_then_reports_a_match(workspace_env) -> None:
    from app.bootstrap import main

    assert main([]) == 0
    assert main(["--check"]) == 0
    assert main([]) == 0, "a second run must validate, not load again"
