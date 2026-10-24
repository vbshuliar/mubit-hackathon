"""Single database-backed worker loop. One process, one worker (docs/05/17):
claim one due job under a short transaction, do its work, mark it DONE or
FAILED. No coroutine sleeps for days; FOLLOW_UP/EXECUTE_ACTION/COORDINATE
are all separate bounded runs woken by rows in `jobs`.
"""
from __future__ import annotations

import asyncio
import logging
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session_scope
from app.domain import services
from app.domain.services import ActorContext
from app.models import CommunicationModel, JobModel
from app.orchestration import dispatcher, executor
from app.orchestration.dispatcher import Coordinator
from app.schemas import CaseStatus

logger = logging.getLogger(__name__)

# >= coordinator.RUN_TIMEOUT_SECONDS (120s) so a COORDINATE job's lease
# can't expire while its run is still legitimately in progress. Only one
# worker task ever runs (see run_worker_loop), so a longer lease isn't a
# double-claim risk here -- it only matters for stale-lease reclaim after a
# crash, which this still bounds.
LEASE_SECONDS = 120
# COORDINATE calls a real model with real network latency (unlike the other
# job kinds, which are local or already have their own retry semantics) --
# a single slow response should not permanently kill a case's progress with
# no automatic retry. Bounded, not unlimited (CLAUDE.md: "bounded retries").
MAX_COORDINATE_ATTEMPTS = 3
COORDINATE_RETRY_DELAY_SECONDS = 5

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def claim_job(session: AsyncSession) -> JobModel | None:
    now = utcnow()
    candidate = (
        await session.execute(
            select(JobModel).where(JobModel.status == "PENDING", JobModel.run_at <= now).order_by(JobModel.run_at).limit(1)
        )
    ).scalars().first()
    if candidate is None:
        candidate = (
            await session.execute(
                select(JobModel).where(JobModel.status == "LEASED", JobModel.lease_until < now).order_by(JobModel.lease_until).limit(1)
            )
        ).scalars().first()
    if candidate is None:
        return None
    candidate.status = "LEASED"
    candidate.lease_until = now + timedelta(seconds=LEASE_SECONDS)
    candidate.attempts += 1
    await session.flush()
    return candidate


async def _handle_follow_up(case_id: str, payload: dict, coordinator: Coordinator) -> None:
    async with session_scope() as session:
        case = await services.load_case(session, case_id)
        if case.status in (CaseStatus.RESOLVED, CaseStatus.CANCELLED):
            return
        event = await services.append_event(
            session, case_id=case_id, event_type="FOLLOW_UP_DUE", payload={"reason": payload.get("reason")},
            actor=ActorContext("SYSTEM", "follow-up-timer", case_id),
            source_event_key=f"followup-due:{case_id}:{utcnow().isoformat()}",
        )
        event_id = event.id

    await dispatcher.run_coordinate(case_id=case_id, trigger_event_id=event_id, coordinator=coordinator)


async def process_one_job(
    coordinator: Coordinator, *, research_adapter=None, raise_on_error: bool = False,
) -> bool:
    """Claims and processes at most one due job. Returns True if a job was
    processed (regardless of success/failure), False if none was due.

    raise_on_error=True (tests only) re-raises instead of swallowing into
    JobModel.last_error -- the production default stays False so one bad
    job can never take down the worker loop."""
    async with session_scope() as session:
        job = await claim_job(session)
        if job is None:
            return False
        job_id, kind, payload, case_id = job.id, job.kind, dict(job.payload or {}), job.case_id

    try:
        if kind == "COORDINATE":
            await dispatcher.run_coordinate(
                case_id=case_id, trigger_event_id=payload["trigger_event_id"], coordinator=coordinator,
            )
        elif kind == "EXECUTE_ACTION":
            await executor.execute_action(
                payload["action_id"], research_adapter=research_adapter,
            )
        elif kind == "FOLLOW_UP":
            await _handle_follow_up(case_id, payload, coordinator)
        elif kind in ("FETCH_RECORDING", "PLACE_CALL"):
            # Historical jobs can never reach a transport after calling removal.
            async with session_scope() as session:
                retired = await session.get(JobModel, job_id)
                retired.status = "FAILED"
                retired.last_error = "Calling was removed; submit a simulated text response instead."
            return True
        else:
            raise ValueError(f"unknown job kind {kind}")

        async with session_scope() as session:
            done_job = await session.get(JobModel, job_id)
            if done_job is not None:
                done_job.status = "DONE"
        return True
    except Exception as exc:  # noqa: BLE001 - isolate one job's failure from the worker loop
        async with session_scope() as session:
            failed_job = await session.get(JobModel, job_id)
            if failed_job is not None:
                failed_job.last_error = f"{exc}\n{traceback.format_exc()}"[:4000]
                from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
                from app.agents.mubit import MubitBudgetExceeded
                exhausted = isinstance(exc, (UnexpectedModelBehavior, UsageLimitExceeded, MubitBudgetExceeded))
                if kind == "COORDINATE" and not exhausted and failed_job.attempts < MAX_COORDINATE_ATTEMPTS:
                    # Retry in place rather than a dead job with no path
                    # back: same row, same dedupe_key, so nothing double-
                    # enqueues it meanwhile.
                    failed_job.status = "PENDING"
                    failed_job.run_at = datetime.now(timezone.utc) + timedelta(seconds=COORDINATE_RETRY_DELAY_SECONDS)
                else:
                    failed_job.status = "FAILED"
        if raise_on_error:
            raise
        return True


async def drain_due_jobs(
    coordinator: Coordinator, *, max_jobs: int = 50,
    research_adapter=None, raise_on_error: bool = False,
) -> int:
    """Test/dev helper: process due jobs synchronously until none remain or
    max_jobs is hit. Returns the number processed."""
    count = 0
    while count < max_jobs:
        processed = await process_one_job(
            coordinator, research_adapter=research_adapter,
            raise_on_error=raise_on_error,
        )
        if not processed:
            break
        count += 1
    return count


# How long a finished job stays on the queue table, and how often the
# worker looks. Finished jobs were never deleted at all: the real
# database accumulated 5,618 rows for 14 cases, 5,601 of them DONE
# FETCH_RECORDING attempts from two calls whose provider lookup failed.
# The sweep that produced them is bounded now, but "bounded" only caps
# the rate -- without retention the table still grows without limit for
# as long as the process runs, and anyone opening the database to
# understand what happened has to read past thousands of dead rows to
# find the handful that matter.
JOB_RETENTION_HOURS = 24 * 7
JOB_RETENTION_SWEEP_INTERVAL_SECONDS = 3600


async def purge_finished_jobs(*, older_than_hours: int = JOB_RETENTION_HOURS) -> int:
    """Deletes DONE jobs past the retention window. Returns how many.

    Only DONE. A FAILED job is evidence of something that went wrong and
    is worth keeping until someone has looked at it; PENDING and RUNNING
    are live work. Deleting a terminal success loses nothing that the
    CaseEvent stream -- the actual audit record -- does not already
    hold, which is why the queue table is safe to trim and the event log
    is not.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
    async with session_scope() as session:
        result = await session.execute(
            sa_delete(JobModel).where(JobModel.status == "DONE", JobModel.run_at < cutoff)
        )
    removed = result.rowcount or 0
    if removed:
        logger.info("purged %s finished job(s) older than %sh", removed, older_than_hours)
    return removed


async def run_worker_loop(
    coordinator: Coordinator, *, stop_event: asyncio.Event,
    research_adapter=None, poll_interval: float = 0.75,
) -> None:
    last_retention_sweep = 0.0
    consecutive_failures = 0
    while not stop_event.is_set():
        # Everything below is inside the guard on purpose. `process_one_job`
        # protects the *job body*, but the claim query that precedes its
        # try block, and maintenance work here, were both outside
        # any handler -- so a SQLite lock contention or an IntegrityError
        # from a dedupe race killed this task outright. It is spawned with
        # `asyncio.create_task` and nothing supervises it, so the failure
        # was silent and total: every job kind simply stopped, with no
        # restart and nothing visible on any case.
        try:
            processed = await process_one_job(
                coordinator,
                research_adapter=research_adapter,
            )

            loop_time = asyncio.get_event_loop().time()
            if loop_time - last_retention_sweep >= JOB_RETENTION_SWEEP_INTERVAL_SECONDS:
                await purge_finished_jobs()
                last_retention_sweep = loop_time
            consecutive_failures = 0
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the loop must outlive any one tick
            consecutive_failures += 1
            logger.exception(
                "worker loop tick failed (%s consecutive); continuing", consecutive_failures
            )
            # Back off rather than spinning on a persistent failure, but
            # never stop: the queue is durable and the condition may clear.
            await asyncio.sleep(min(poll_interval * consecutive_failures, 30.0))
            continue

        if not processed:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=poll_interval)
            except asyncio.TimeoutError:
                pass
