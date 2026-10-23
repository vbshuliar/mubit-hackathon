"""Anthropic through Mubit, with per-case sessions and content-free run metrics."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from contextvars import ContextVar
from contextlib import closing
from datetime import datetime, timezone

import httpx2
from anthropic import AsyncAnthropic
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import RunUsage, UsageLimits

from app.agents.coordinator import GeminiCoordinator, construct_agent, MAX_MODEL_REQUESTS, MAX_TOOL_CALLS
from app.agents.instructions import COORDINATOR_PROMPT_VERSION
from app.config import Settings

logger = logging.getLogger(__name__)
_request_ids: ContextVar[list[str] | None] = ContextVar("mubit_request_ids", default=None)


class MubitBudgetExceeded(RuntimeError):
    """Paid execution is paused; never silently substitute a different model."""


def reserve_run(settings: Settings) -> int:
    """Reserve before network I/O, including failed runs and interrupted processes.

    SQLite serializes concurrent reservations and survives app restarts. This is
    a run-count guard, not a provider billing balance or a dollar-cost estimate.
    Token limits are checked after responses and may overshoot by one response.
    """
    settings.mubit_budget_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(settings.mubit_budget_path, timeout=5)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL)")
        db.execute("BEGIN IMMEDIATE")
        used = db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
        if used >= settings.mubit_max_runs:
            raise MubitBudgetExceeded(
                f"Mubit live-run limit reached ({used}/{settings.mubit_max_runs}). "
                "Paid calls are paused. Review usage before increasing MUBIT_MAX_RUNS."
            )
        db.execute("INSERT INTO reservations(created_at) VALUES (?)", (datetime.now(timezone.utc).isoformat(),))
        return used + 1


async def capture_request_id(response: httpx2.Response) -> None:
    ids = _request_ids.get()
    request_id = response.headers.get("x-middleware-request-id")
    if ids is not None and request_id:
        ids.append(request_id)


class MubitCoordinator(GeminiCoordinator):
    def __init__(self, settings: Settings, *, http_client=None):
        self.settings = settings
        client = AsyncAnthropic(
            api_key=settings.mubit_api_key.get_secret_value(),
            base_url=settings.mubit_base_url,
            max_retries=0,  # worker and agent already own bounded retries
            http_client=http_client or httpx2.AsyncClient(event_hooks={"response": [capture_request_id]}),
        )
        self.client = client
        agent = construct_agent(AnthropicModel(settings.mubit_model, provider=AnthropicProvider(anthropic_client=client)))
        super().__init__(agent, model_id=f"mubit/anthropic/{settings.mubit_model}")
        self.usage_limits = UsageLimits(
            request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS,
            total_tokens_limit=settings.mubit_max_tokens_per_run,
        )

    async def aclose(self) -> None:
        await self.client.close()

    async def decide(self, snapshot, trigger_event_id):
        ids: list[str] = []
        token = _request_ids.set(ids)
        started = time.perf_counter()
        usage = RunUsage()
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": str(snapshot.case.id), "trigger_event_id": str(trigger_event_id),
            "model_id": self.model_id, "prompt_version": COORDINATOR_PROMPT_VERSION,
            "record_mode": self.settings.mubit_record, "status": "failed",
        }
        try:
            metrics["reserved_run"] = reserve_run(self.settings)
            metrics["live_run_limit"] = self.settings.mubit_max_runs
            result = await self._run(snapshot, trigger_event_id, AnthropicModelSettings(
                max_tokens=4096,
                anthropic_metadata={"user_id": f"repairflow-case-{snapshot.case.id}"},
                extra_headers={"x-middleware-record": self.settings.mubit_record},
            ), usage=usage)
            usage = result.usage
            metrics.update(status="validated_proposal", action=result.output.action.kind,
                           requests=usage.requests, input_tokens=usage.input_tokens,
                           output_tokens=usage.output_tokens)
            if self.settings.mubit_report_shadow_enabled:
                # Import lazily: the focused task shares this module's budget guard.
                from app.agents.report_routing import observe_report
                metrics["report_shadow"] = await observe_report(snapshot, self.settings)
            return result.output
        except BaseException as exc:
            metrics["error_type"] = type(exc).__name__
            if isinstance(exc, UsageLimitExceeded):
                # The SDK exposes no structured limit category. Persist only a
                # known category, never its exception message or provider content.
                metrics["limit_kind"] = next((name for name in (
                    "request_limit", "tool_calls_limit", "input_tokens_limit",
                    "output_tokens_limit", "total_tokens_limit", "cost_limit",
                ) if name in str(exc)), "unknown")
            raise
        finally:
            metrics.update(requests=usage.requests, input_tokens=usage.input_tokens,
                           output_tokens=usage.output_tokens, tool_calls=usage.tool_calls)
            metrics.update(elapsed_ms=round((time.perf_counter() - started) * 1000), request_ids=ids)
            _request_ids.reset(token)
            # Never store prompts, replies, secrets, or provider exception bodies here.
            # A valid proposal is not evidence that policy admitted it or work succeeded.
            try:
                self.settings.data_dir.mkdir(parents=True, exist_ok=True)
                path = self.settings.data_dir / "mubit-runs.jsonl"
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                with os.fdopen(fd, "a") as stream:
                    stream.write(json.dumps(metrics) + "\n")
            except OSError:
                logger.exception("Could not persist Mubit run metrics")
