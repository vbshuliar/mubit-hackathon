"""CLI for the workspace snapshot.

    python -m app.workspace --export     # capture THIS database into backend/snapshot/
    python -m app.workspace --apply      # load the snapshot into an empty database
    python -m app.workspace --replace    # back up the database, empty it, load the snapshot
    python -m app.workspace --validate   # is this database exactly the snapshot?

`--export` is the only one that writes into the source tree. Run it on
the machine whose database is the source of truth, then commit
`backend/snapshot/`. Most people want `python -m app.bootstrap`, which
wraps `--apply` and `--validate`.

Stop the server before `--replace`: it empties tables the running worker
may be writing to.
"""

from __future__ import annotations

import argparse
import sys

from app.workspace import DatabaseNotEmpty, apply_snapshot, ensure_schema, validate


def _print_report() -> int:
    report = validate()
    for c in report.checks:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")
    return 0 if report.passed else 1


def _apply(replace: bool) -> int:
    ensure_schema()
    try:
        result = apply_snapshot(replace=replace)
    except DatabaseNotEmpty as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if result.backup:
        print(f"Previous database copied to {result.backup}")
    print(f"Snapshot loaded: {result.rows} row(s), {result.files} file(s) copied.")
    return 0


def _export() -> int:
    from app.workspace.export import MissingFile, PersonalDataFound, export

    try:
        path, tables = export()
    except (PersonalDataFound, MissingFile) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    total = sum(len(v) for v in tables.values())
    print(f"Captured {total} row(s) across {len(tables)} table(s) -> {path}")
    for name, rows in tables.items():
        print(f"  {name}: {len(rows)}")
    print("\nCommit backend/snapshot/ so a clone reproduces this database.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.workspace", description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export", action="store_true", help="Capture this database into backend/snapshot/.")
    group.add_argument("--apply", action="store_true", help="Load the snapshot into an empty database.")
    group.add_argument("--replace", action="store_true", help="Back up, empty, then load the snapshot.")
    group.add_argument("--validate", action="store_true", help="Check this database is exactly the snapshot.")
    args = parser.parse_args(argv)

    if args.export:
        return _export()
    if args.apply or args.replace:
        return _apply(replace=args.replace)
    ensure_schema()
    return _print_report()


if __name__ == "__main__":
    sys.exit(main())
