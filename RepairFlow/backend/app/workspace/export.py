"""Write this machine's database out as `backend/snapshot/workspace.sql`.

Run this on the machine whose database is the source of truth:

    uv run python -m app.workspace --export

It reads every content table in one read transaction, writes one
`INSERT` per row in foreign-key order, and copies every file a row
points at into `backend/snapshot/files/`. The output is deterministic --
rows ordered by primary key, columns in model order -- so re-exporting an
unchanged database produces an identical file and an empty git diff.

Values are written exactly as SQLite stores them. Timestamps, JSON and
booleans are TEXT/INTEGER in the file already, so nothing is parsed or
re-serialised on the way out or back in, and a restored database holds
the same bytes the source did.

## The personal-data gate

Before writing, every string in the payload is scanned for:

  - phone numbers that are not one of the placeholder ranges `app.seed`
    uses,
  - email addresses,
  - anything that looks like an API key or bearer token.

A hit aborts the export and names the table, column and row. There is
deliberately no override flag: if real data needs to ship, the fix is to
change the data, not to silence the check.

One value is redacted rather than refused, because the owner has decided
it stays on their machine: a real mobile number hand-edited into one
`tenants` row so live calls reach a test phone. A tenant whose number is
not a placeholder is written with the placeholder `app.seed` gives that
tenant, which is exactly what a clone had before this snapshot existed.
A tenant `app.seed` does not know has no placeholder to fall back on, so
its number is left alone and the gate refuses it.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.config import get_settings
from app.workspace import (
    SNAPSHOT_DIR,
    SQL_NAME,
    TABLE_ORDER,
    column_order,
    primary_key,
    referenced_files,
)


class PersonalDataFound(RuntimeError):
    """Raised instead of writing a snapshot that carries personal data."""


class MissingFile(RuntimeError):
    """Raised when a row points at a file that is not on this disk."""


# `app.seed` issues placeholder numbers in +4411xxxxxxxx. Anything else
# that looks like a phone number did not come from the generator.
_PLACEHOLDER_PHONE = re.compile(r"^\+4411\d{6,8}$")
_PHONE = re.compile(r"\+\d[\d\s().-]{7,}\d")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")
# sk-..., xi-..., AIza..., ghp_..., and long opaque bearer-ish blobs.
_SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xi-[A-Za-z0-9]{16,})\b")


def _seed_phones() -> dict[str, str]:
    from app.seed import TENANTS

    return {t["id"]: t["phone_e164"] for t in TENANTS}


def redact(table: str, row: dict[str, Any]) -> dict[str, Any]:
    """Swap a real tenant number for that tenant's `app.seed` placeholder."""
    if table != "tenants":
        return row
    phone = row.get("phone_e164")
    if not phone or _PLACEHOLDER_PHONE.match(phone):
        return row
    placeholder = _seed_phones().get(row.get("id"))
    if placeholder is None:
        return row  # nothing to fall back on: let the gate refuse it
    return {**row, "phone_e164": placeholder}


def _scan_value(value: Any) -> list[str]:
    """Return a list of reasons this value must not be committed."""
    if value is None:
        return []
    if isinstance(value, (dict, list)):
        text = json.dumps(value)
    elif isinstance(value, str):
        text = value
    else:
        return []

    reasons: list[str] = []
    for match in _PHONE.findall(text):
        compact = re.sub(r"[\s().-]", "", match)
        if not _PLACEHOLDER_PHONE.match(compact):
            reasons.append(f"non-placeholder phone number ending {compact[-4:]}")
    if _EMAIL.search(text):
        reasons.append("email address")
    if _SECRET.search(text):
        reasons.append("possible API key or token")
    return reasons


def scan_tables(tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Every reason the payload must not be written, with a location."""
    problems: list[str] = []
    for table, rows in tables.items():
        for row in rows:
            for column, value in row.items():
                for reason in _scan_value(value):
                    problems.append(f"{table}.{column} (row id {str(row.get('id'))[:8]}...): {reason}")
    return problems


def literal(value: Any) -> str:
    """One SQLite literal, always on a single line.

    A text value containing a line break is written as quoted pieces
    joined by `char(13)`/`char(10)`, so every row stays on one line -- which
    is what makes the file diffable and lets a row be compared as a line.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, bytes):
        return f"X'{value.hex()}'"
    parts = re.split(r"(\r\n|\r|\n)", str(value))
    pieces = []
    for part in parts:
        if part == "\r\n":
            pieces.append("char(13,10)")
        elif part == "\r":
            pieces.append("char(13)")
        elif part == "\n":
            pieces.append("char(10)")
        elif part or len(parts) == 1:
            pieces.append("'" + part.replace("'", "''") + "'")
    return " || ".join(pieces)


def read_tables(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    """Every content row, redacted, in primary-key order. One read transaction."""
    tables: dict[str, list[dict[str, Any]]] = {}
    connection.execute("BEGIN")
    try:
        for table in TABLE_ORDER:
            present = {r[1] for r in connection.execute(f'PRAGMA table_info("{table}")')}
            columns = [c for c in column_order(table) if c in present]
            if not columns:
                continue
            order = ", ".join(f'"{c}"' for c in primary_key(table))
            select = ", ".join(f'"{c}"' for c in columns)
            cursor = connection.execute(f'SELECT {select} FROM "{table}" ORDER BY {order}')
            rows = [redact(table, dict(zip(columns, r))) for r in cursor]
            if rows:
                tables[table] = rows
    finally:
        connection.execute("COMMIT")
    return tables


def render_sql(tables: dict[str, list[dict[str, Any]]]) -> str:
    counts = ", ".join(f"{t} {len(rows)}" for t, rows in tables.items())
    lines = [
        "-- The shared RepairFlow workspace: every row of every content table.",
        "-- Generated by `uv run python -m app.workspace --export`; do not hand-edit.",
        "-- Load it with `uv run python -m app.bootstrap` (see SETUP.md).",
        "-- The `jobs` queue is runtime state and is never captured.",
        f"-- Rows: {counts}",
        "BEGIN;",
        # case_events.causation_event_id points into its own table, so rows
        # cannot all arrive after the row they reference. Deferring the
        # check to COMMIT lets them load in key order and still be verified.
        "PRAGMA defer_foreign_keys=ON;",
    ]
    for table, rows in tables.items():
        lines.append(f"-- {table}: {len(rows)}")
        columns = ", ".join(f'"{c}"' for c in rows[0])
        for row in rows:
            values = ", ".join(literal(v) for v in row.values())
            lines.append(f'INSERT INTO "{table}" ({columns}) VALUES ({values});')
    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def connect_readonly(path: Path) -> sqlite3.Connection:
    """Read-only, so exporting from a database the server is using is safe."""
    uri = f"file:{quote(Path(path).resolve().as_posix(), safe='/:')}?mode=ro"
    return sqlite3.connect(uri, uri=True, isolation_level=None)


def export(snapshot_dir: Path | None = None, database_path: Path | None = None) -> tuple[Path, dict[str, list[dict[str, Any]]]]:
    settings = get_settings()
    target = snapshot_dir or SNAPSHOT_DIR
    connection = connect_readonly(database_path or settings.database_path)
    try:
        tables = read_tables(connection)
    finally:
        connection.close()

    problems = scan_tables(tables)
    if problems:
        raise PersonalDataFound(
            f"Refusing to write {SQL_NAME}: it would publish personal data.\n  "
            + "\n  ".join(problems[:20])
            + (f"\n  ... and {len(problems) - 20} more" if len(problems) > 20 else "")
        )

    sources = {"documents": settings.documents_dir, "recordings": settings.recordings_dir}
    wanted = referenced_files(tables)
    missing = [f"{kind}/{name}" for kind, name in wanted if not (sources[kind] / name).is_file()]
    if missing:
        raise MissingFile("Rows point at files that are not on this disk:\n  " + "\n  ".join(missing))

    target.mkdir(parents=True, exist_ok=True)
    (target / SQL_NAME).write_text(render_sql(tables), encoding="utf-8", newline="\n")

    # Mirror exactly the referenced files: copy what is new or changed,
    # delete what no row points at any more.
    for kind, source in sources.items():
        names = {name for k, name in wanted if k == kind}
        folder = target / "files" / kind
        if names:
            folder.mkdir(parents=True, exist_ok=True)
        for name in names:
            src, dst = source / name, folder / name
            if not dst.is_file() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)
        if folder.is_dir():
            for stale in folder.iterdir():
                if stale.name not in names:
                    stale.unlink()
    return target / SQL_NAME, tables
