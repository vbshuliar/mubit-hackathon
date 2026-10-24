"""The whole shared workspace, committed as SQL so a clone reproduces it exactly.

`backend/data/` is gitignored, so a clone starts with no database. This
package closes that gap completely: `backend/snapshot/workspace.sql`
holds every row of every content table, `backend/snapshot/files/` holds
every file those rows point at, and loading them into an empty database
gives a clone the same properties, tenants, contractors, cases, events,
messages, costs, notes, documents and timestamps as the machine that
exported them -- byte for byte, not merely the same counts.

It replaces two weaker arrangements. The generators (`app.seed`,
`app.archive`, `app.sample_operations`) reproduce their content but
date it relative to *when they run*, so a clone made a month later had
every generated case shifted by a month; and anything changed through
the running application on a generated case was never captured at all.
`app.intake_fixture` captured only the fourteen cases nobody generated.
The generators remain the way new synthetic data is authored; this
snapshot is what everyone loads.

Two things are deliberately not carried:

  - `jobs`, the durable wake-up queue. It is runtime retry state, not
    content, and replaying it on a clone would wake the agent against
    cases on someone else's machine.
  - one real tenant phone number, which the owner keeps on their own
    machine; see `export.redact`.

    uv run python -m app.workspace --export     # capture THIS database
    uv run python -m app.workspace --apply      # load into an empty database
    uv run python -m app.workspace --replace    # back up, wipe, then load
    uv run python -m app.workspace --validate   # is this database the snapshot?
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import models  # noqa: F401  register every table on Base.metadata
from app.config import BACKEND_DIR, get_settings
from app.db import Base

SNAPSHOT_DIR = BACKEND_DIR / "snapshot"
SQL_NAME = "workspace.sql"

# Runtime state, not content -- see the module docstring.
EXCLUDED_TABLES = frozenset({"jobs"})

# Foreign-key order, derived from the schema rather than hand-listed: a
# hand-written list got `dependencies` before `contractor_reports` once
# and failed only at import time. Deletion walks it in reverse.
TABLE_ORDER: tuple[str, ...] = tuple(
    t.name for t in Base.metadata.sorted_tables if t.name not in EXCLUDED_TABLES
)


def column_order(table: str) -> list[str]:
    return [c.name for c in Base.metadata.tables[table].columns]


def primary_key(table: str) -> list[str]:
    return [c.name for c in Base.metadata.tables[table].primary_key.columns]


def ensure_schema() -> None:
    """Create or upgrade the schema, then let go of the engine.

    The snapshot is plain INSERTs into the application's own schema, so a
    column added to the models since the export simply takes its default.
    `run_cli` runs `create_all()` before awaiting what it is given; the
    engine is disposed so the file is free for the sqlite3 work after.
    """
    from app.db import dispose_engine, run_cli

    run_cli(dispose_engine())


def snapshot_sql_path(snapshot_dir: Path | None = None) -> Path:
    return (snapshot_dir or SNAPSHOT_DIR) / SQL_NAME


def referenced_files(tables: dict[str, list[dict[str, Any]]]) -> list[tuple[str, str]]:
    """(kind, filename) for every file a row points at.

    `documents.stored_name` lives in DOCUMENTS_DIR; a communication whose
    recording was acquired names its audio in RECORDINGS_DIR. Nothing
    else in the schema refers to a file on disk -- property photos are
    frontend assets, committed with the frontend.
    """
    wanted: list[tuple[str, str]] = []
    for row in tables.get("documents", []):
        if row.get("stored_name"):
            wanted.append(("documents", row["stored_name"]))
    for row in tables.get("communications", []):
        recording = row.get("recording")
        if isinstance(recording, str):
            try:
                recording = json.loads(recording)
            except ValueError:
                recording = None
        if isinstance(recording, dict) and recording.get("status") == "AVAILABLE" and recording.get("media_path"):
            wanted.append(("recordings", recording["media_path"]))
    return sorted(set(wanted))


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, isolation_level=None)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _snapshot_files(snapshot_dir: Path) -> list[tuple[str, Path]]:
    root = snapshot_dir / "files"
    out: list[tuple[str, Path]] = []
    for kind in ("documents", "recordings"):
        folder = root / kind
        if folder.is_dir():
            out.extend((kind, p) for p in sorted(folder.iterdir()) if p.is_file())
    return out


def _destinations() -> dict[str, Path]:
    settings = get_settings()
    return {"documents": settings.documents_dir, "recordings": settings.recordings_dir}


def content_row_count(database_path: Path | None = None) -> int:
    path = database_path or get_settings().database_path
    connection = _connect(path)
    try:
        existing = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return sum(
            connection.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            for t in TABLE_ORDER
            if t in existing
        )
    finally:
        connection.close()


class DatabaseNotEmpty(RuntimeError):
    """Raised by apply() rather than mixing the snapshot into existing data."""


@dataclass
class ApplyResult:
    rows: int = 0
    files: int = 0
    backup: Path | None = None


def apply_snapshot(
    snapshot_dir: Path | None = None,
    database_path: Path | None = None,
    *,
    replace: bool = False,
) -> ApplyResult:
    """Load the snapshot. The schema must already exist (run_cli creates it).

    Refuses a database that already holds content: half-merging the
    snapshot into someone's own rows would produce a database that
    matches neither. `replace=True` copies the current file aside first,
    then empties every table (including `jobs`, whose rows point at the
    cases being replaced) and loads.
    """
    source_dir = snapshot_dir or SNAPSHOT_DIR
    sql = snapshot_sql_path(source_dir).read_text(encoding="utf-8")
    path = database_path or get_settings().database_path
    result = ApplyResult()

    if content_row_count(path):
        if not replace:
            raise DatabaseNotEmpty(
                f"{path} already holds data. Use --replace to back it up and load the snapshot instead."
            )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        result.backup = path.with_name(f"{path.name}.before-replace-{stamp}")
        source, copy = sqlite3.connect(path), sqlite3.connect(result.backup)
        try:
            source.backup(copy)
        finally:
            copy.close()
            source.close()
        connection = _connect(path)
        try:
            connection.execute("BEGIN")
            for table in ("jobs", *reversed(TABLE_ORDER)):
                connection.execute(f'DELETE FROM "{table}"')
            connection.execute("COMMIT")
        finally:
            connection.close()

    connection = _connect(path)
    try:
        # Foreign keys are ON and deferred to COMMIT by the script itself,
        # so a snapshot that does not hang together fails here, loudly,
        # rather than loading.
        connection.executescript(sql)
        result.rows = sum(
            connection.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in TABLE_ORDER
        )
    finally:
        connection.close()

    for kind, src in _snapshot_files(source_dir):
        folder = _destinations()[kind]
        folder.mkdir(parents=True, exist_ok=True)
        dst = folder / src.name
        if not dst.is_file() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
            result.files += 1
    return result


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def _insert_lines(sql: str) -> dict[str, set[str]]:
    by_table: dict[str, set[str]] = {}
    for line in sql.splitlines():
        if line.startswith('INSERT INTO "'):
            table = line[len('INSERT INTO "') :].split('"', 1)[0]
            by_table.setdefault(table, set()).add(line)
    return by_table


def validate(snapshot_dir: Path | None = None, database_path: Path | None = None) -> Report:
    """Is this database exactly the snapshot? Compared row by row, as SQL.

    The database is rendered with the same writer `--export` uses and the
    two files are compared line by line. One line is one row, so a row
    that differs in any column shows up as one snapshot row absent and
    one database row extra.
    """
    from app.workspace.export import connect_readonly, read_tables, render_sql

    source_dir = snapshot_dir or SNAPSHOT_DIR
    report = Report()
    sql_path = snapshot_sql_path(source_dir)
    if not sql_path.is_file():
        report.checks.append(Check("snapshot_present", False, f"{sql_path} is missing"))
        return report
    expected = _insert_lines(sql_path.read_text(encoding="utf-8"))
    total = sum(len(v) for v in expected.values())
    report.checks.append(
        Check("snapshot_present", True, f"{total} row(s) across {len(expected)} table(s)")
    )

    connection = connect_readonly(database_path or get_settings().database_path)
    try:
        actual = _insert_lines(render_sql(read_tables(connection)))
    finally:
        connection.close()

    absent = {t: len(rows - actual.get(t, set())) for t, rows in expected.items()}
    extra = {t: len(rows - expected.get(t, set())) for t, rows in actual.items()}
    absent = {t: n for t, n in absent.items() if n}
    extra = {t: n for t, n in extra.items() if n}
    if not absent and not extra:
        detail = f"all {total} row(s) identical"
    else:
        detail = (
            f"{sum(absent.values())} snapshot row(s) absent or different, "
            f"{sum(extra.values())} database row(s) not in the snapshot "
            f"(tables: {', '.join(sorted(set(absent) | set(extra)))})"
        )
    report.checks.append(Check("database_matches_snapshot", not absent and not extra, detail))

    destinations = _destinations()
    files = _snapshot_files(source_dir)
    wrong = [
        f"{kind}/{src.name}"
        for kind, src in files
        if not (destinations[kind] / src.name).is_file()
        or (destinations[kind] / src.name).read_bytes() != src.read_bytes()
    ]
    report.checks.append(
        Check(
            "every_snapshot_file_is_on_disk",
            not wrong,
            f"{len(files) - len(wrong)}/{len(files)} file(s) present and byte-identical"
            + (f"; wrong or missing: {', '.join(wrong[:5])}" if wrong else ""),
        )
    )
    return report
