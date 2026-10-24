"""Bring a database up to the shared workspace, in one command.

    uv run python -m app.bootstrap            # empty database -> the shared workspace
    uv run python -m app.bootstrap --check    # write nothing; does this database match?
    uv run python -m app.bootstrap --replace  # copy yours aside, then load the workspace

The workspace is `backend/snapshot/workspace.sql` plus the files in
`backend/snapshot/files/` -- every row of every content table, exported
from the machine that is the source of truth (see `app.workspace`).
Loading it into an empty database and then validating it row by row is
the whole job; a database that passes is identical to the source, not
merely the same size.

It used to run the generators (`app.seed`, `app.intake_fixture`,
`app.archive`, `app.sample_operations`, `app.backfill_case_history`) in
a load-bearing order instead. That reproduced the content but not the
dates -- generated cases were anchored to when bootstrap ran, so a clone
made a month later disagreed with the source on every one of them -- and
it could not carry anything changed through the running application.
The generators remain how new synthetic data is authored; after
authoring, `python -m app.workspace --export` captures the result.

A database that already holds data is never merged into. Bootstrap
validates it and says how it differs; `--replace` is the explicit way to
discard it, and copies the file aside first.
"""

from __future__ import annotations

import argparse
import sys


async def _counts() -> dict[str, int]:
    import sqlalchemy as sa

    from app.db import session_scope
    from app.models import (
        ContractorModel,
        PropertyModel,
        RepairCaseModel,
        TenantModel,
    )

    async with session_scope() as session:

        async def count(model, *where) -> int:
            return (
                await session.execute(sa.select(sa.func.count()).select_from(model).where(*where))
            ).scalar_one()

        return {
            "properties": await count(PropertyModel),
            "tenants": await count(TenantModel),
            "contractors": await count(ContractorModel),
            "cases (total)": await count(RepairCaseModel),
            "cases (operational)": await count(
                RepairCaseModel, RepairCaseModel.archive_batch_id.is_(None)
            ),
            "cases (archival)": await count(
                RepairCaseModel, RepairCaseModel.archive_batch_id.is_not(None)
            ),
        }


def _print_counts(heading: str) -> None:
    from app.db import run_cli

    print(f"\n{heading}")
    for name, value in run_cli(_counts()).items():
        print(f"  {name:<22}{value:>6}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.bootstrap", description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="Write nothing; report whether this database matches."
    )
    mode.add_argument(
        "--replace",
        action="store_true",
        help="Copy the current database aside, empty it, and load the workspace. Stop the server first.",
    )
    args = parser.parse_args(argv)

    from app.workspace import (
        apply_snapshot,
        content_row_count,
        ensure_schema,
        validate,
    )

    ensure_schema()

    if args.replace or (not args.check and content_row_count() == 0):
        result = apply_snapshot(replace=args.replace)
        if result.backup:
            print(f"Previous database copied to {result.backup}")
        print(f"Loaded the shared workspace: {result.rows} row(s), {result.files} file(s).")
    elif not args.check:
        print("This database already holds data, so nothing was loaded. Checking it instead.")

    print("\nValidating against backend/snapshot/:")
    report = validate()
    for c in report.checks:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")

    _print_counts("Database:")

    if not report.passed:
        print(
            "\nThis database is not the shared workspace. To make it identical, stop the\n"
            "server and run `uv run python -m app.bootstrap --replace` (your current file\n"
            "is copied aside first). If YOUR data is what everyone should have, run\n"
            "`uv run python -m app.workspace --export` and commit backend/snapshot/ instead.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
