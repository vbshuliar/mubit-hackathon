"""Content-free evidence of actual Pydantic AI read-tool attempts."""
from __future__ import annotations

import uuid

from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart, RetryPromptPart

from app.schemas import ToolTrace, ToolTraceOutcome

READ_TOOLS = frozenset({"read_report", "read_communication", "list_case_events", "find_appointment_options", "read_research"})


def _resource_ids(value) -> list[str]:
    ids = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "id" or key.endswith("_id"):
                try:
                    ids.append(str(uuid.UUID(str(item))))
                except (ValueError, TypeError, AttributeError):
                    pass
            elif isinstance(item, dict):
                ids.extend(_resource_ids(item))
    return sorted(set(ids))


def build_tool_traces(messages, run_id: str) -> list[dict]:
    """Output calls are proposals, not reads. Never persist raw text/arguments.

    Timestamps are the local model response and tool return timestamps supplied by
    Pydantic AI, not invented timing measurements. A call without a return remains
    unfinished, including when an outer run was interrupted.
    """
    traces: dict[str, ToolTrace] = {}
    for message in messages:
        for part in message.parts:
            if isinstance(message, ModelResponse) and isinstance(part, ToolCallPart) and part.tool_name in READ_TOOLS:
                try:
                    ids = _resource_ids(part.args_as_dict())
                except (ValueError, TypeError):
                    ids = []
                traces[part.tool_call_id] = ToolTrace(
                    id=uuid.uuid4(), run_id=run_id, name=part.tool_name,
                    started_at=message.timestamp, input_resource_ids=ids,
                )
            elif isinstance(part, (ToolReturnPart, RetryPromptPart)) and part.tool_call_id in traces:
                trace = traces[part.tool_call_id]
                failed = isinstance(part, RetryPromptPart) or getattr(part, "outcome", "success") == "failed"
                trace.finished_at = part.timestamp
                trace.outcome = ToolTraceOutcome.FAILED if failed else ToolTraceOutcome.SUCCEEDED
                trace.error_code = "TOOL_RETRY_OR_FAILURE" if failed else None
    return [trace.model_dump(mode="json") for trace in traces.values()]


# Only fixed application-owned validator prefixes map to persistent codes. The
# trailing text can contain evidence or identifiers and must never be stored.
_VALIDATOR_FAILURE_PREFIXES = (
    ("Critical safety answers are still UNKNOWN.", "LAST_OBSERVED_VALIDATION_SAFETY_UNKNOWN"),
    ("Ask every unanswered safety category explicitly before progressing.", "LAST_OBSERVED_VALIDATION_SAFETY_QUESTION_COVERAGE"),
    ("Recorded safety concern ", "LAST_OBSERVED_VALIDATION_SAFETY_DOWNGRADE"),
    ("Safety answer ", "LAST_OBSERVED_VALIDATION_SAFETY_UNCONFIRMED"),
    ("Work orders already exist.", "LAST_OBSERVED_VALIDATION_REDUNDANT_TRIAGE"),
    ("Only PENDING reports may be interpreted.", "LAST_OBSERVED_VALIDATION_REPORT_NOT_PENDING"),
    ("A newer report was received for this appointment.", "LAST_OBSERVED_VALIDATION_REPORT_SUPERSEDED"),
    ("COMPLETED requires completion_evidence_refs", "LAST_OBSERVED_VALIDATION_COMPLETION_EVIDENCE"),
    ("This report mentions access equipment.", "LAST_OBSERVED_VALIDATION_ACCESS_CLASSIFICATION"),
    ("Before SCHEDULE_VISIT call find_appointment_options", "LAST_OBSERVED_VALIDATION_SLOT_NOT_OFFERED"),
    ("Use the current case ID and snapshot version exactly.", "LAST_OBSERVED_VALIDATION_CASE_VERSION"),
    ("Approved contractors already cover this trade and postcode.", "LAST_OBSERVED_VALIDATION_UNNECESSARY_RESEARCH"),
    ("Research for this trade already completed.", "LAST_OBSERVED_VALIDATION_REPEATED_RESEARCH"),
    ("The repair is not ready for closure.", "LAST_OBSERVED_VALIDATION_PREMATURE_CLOSURE"),
    ("A contractor report is not tenant confirmation.", "LAST_OBSERVED_VALIDATION_CONFIRMATION_REQUIRED"),
    ("Copy the latest affirmative TENANT_CONFIRMATION_RECEIVED", "LAST_OBSERVED_VALIDATION_CONFIRMATION_REFERENCE"),
    ("FOLLOW_UP is reserved for tenant resolution confirmation", "LAST_OBSERVED_VALIDATION_REQUEST_PURPOSE"),
    ("Contractor report questions must target OPERATOR", "LAST_OBSERVED_VALIDATION_REQUEST_RECIPIENT"),
    ("REQUEST_INFORMATION must contain explicit, non-empty questions.", "LAST_OBSERVED_VALIDATION_EMPTY_QUESTIONS"),
)


def validator_failure_code(messages) -> str | None:
    """Label the latest captured retry, never claim it is the terminal cause.

    Retry exhaustion may raise before the final rejection is captured. Codes
    explicitly say LAST_OBSERVED to preserve that uncertainty.
    Unknown retry text and structured schema errors retain the dispatcher's
    exception-class fallback; an earlier, corrected retry is not substituted.
    """
    for message in reversed(messages):
        for part in reversed(message.parts):
            if isinstance(part, RetryPromptPart):
                if not isinstance(part.content, str):
                    return None
                return next((code for prefix, code in _VALIDATOR_FAILURE_PREFIXES
                             if part.content.startswith(prefix)), None)
    return None
