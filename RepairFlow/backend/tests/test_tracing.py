import uuid

import pytest

from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart, RetryPromptPart

from app.agents.tracing import build_tool_traces


def test_actual_reads_are_recorded_without_content():
    run_id, case_id, report_id = [str(uuid.uuid4()) for _ in range(3)]
    messages = [
        ModelResponse(parts=[ToolCallPart("read_report", {"ref": {"case_id": case_id, "record_id": report_id}}, "a")]),
        ModelRequest(parts=[ToolReturnPart("read_report", "private report text", "a")]),
        ModelResponse(parts=[ToolCallPart("final_result", {"decision_summary": "private"}, "b")]),
    ]
    traces = build_tool_traces(messages, run_id)
    assert len(traces) == 1
    assert traces[0]["name"] == "read_report"
    assert traces[0]["run_id"] == run_id
    assert traces[0]["outcome"] == "SUCCEEDED"
    assert traces[0]["input_resource_ids"] == sorted([case_id, report_id])
    assert "private" not in str(traces)


def test_retries_and_unfinished_calls_are_honest():
    messages = [
        ModelResponse(parts=[ToolCallPart("read_report", "invalid-json", "a")]),
        ModelRequest(parts=[RetryPromptPart("private validation reason", tool_name="read_report", tool_call_id="a")]),
        ModelResponse(parts=[ToolCallPart("find_appointment_options", {}, "b")]),
    ]
    traces = build_tool_traces(messages, str(uuid.uuid4()))
    assert traces[0]["outcome"] == "FAILED"
    assert traces[1]["outcome"] is None
    assert traces[1]["finished_at"] is None
    assert "private" not in str(traces)


def test_validator_failure_codes_do_not_contain_retry_content():
    from app.agents.tracing import validator_failure_code

    prefixes = [
        ('Ask every unanswered safety category explicitly before progressing.', 'LAST_OBSERVED_VALIDATION_SAFETY_QUESTION_COVERAGE'),
        ('Work orders already exist.', 'LAST_OBSERVED_VALIDATION_REDUNDANT_TRIAGE'),
        ('COMPLETED requires completion_evidence_refs', 'LAST_OBSERVED_VALIDATION_COMPLETION_EVIDENCE'),
        ('Before SCHEDULE_VISIT call find_appointment_options', 'LAST_OBSERVED_VALIDATION_SLOT_NOT_OFFERED'),
    ]
    for prefix, expected in prefixes:
        messages = [ModelRequest(parts=[RetryPromptPart(prefix + ' private-address secret-token')])]
        code = validator_failure_code(messages)
        assert code == expected
        assert 'private' not in code and 'secret' not in code


def test_latest_unknown_retry_does_not_reuse_earlier_failure():
    from app.agents.tracing import validator_failure_code

    messages = [ModelRequest(parts=[
        RetryPromptPart('Work orders already exist.'),
        RetryPromptPart('Provider error with secret-token'),
    ])]
    assert validator_failure_code(messages) is None
    assert validator_failure_code([]) is None
    assert validator_failure_code([ModelResponse(parts=[ToolCallPart('final_result', {'text': 'Work orders already exist.'})])]) is None


def test_schema_retry_is_not_persisted_as_validator_text():
    from app.agents.tracing import validator_failure_code

    messages = [ModelRequest(parts=[RetryPromptPart([{
        'type': 'missing', 'loc': ('private_field',), 'input': 'secret-token'}])])]
    assert validator_failure_code(messages) is None


async def _assert_dispatcher_failure_code(monkeypatch, error, expected):
    from contextlib import contextmanager
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import select
    import pydantic_ai
    from app.db import session_scope
    from app.main import app
    from app.models import OrchestrationRunModel
    from app.orchestration.dispatcher import run_coordinate
    from app.domain import services
    from tests.test_demo_inputs import create

    @contextmanager
    def captured():
        yield [ModelRequest(parts=[RetryPromptPart('Work orders already exist. private-secret')])]

    class FailingCoordinator:
        model_id = 'offline-test'

        async def decide(self, snapshot, trigger_event_id):
            raise error

    monkeypatch.setattr(pydantic_ai, 'capture_run_messages', captured)
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid = await create(client)
    async with session_scope() as session:
        snapshot = await services.load_case_snapshot(session, cid)
        event_id = str(snapshot.recent_events[0].id)
    with pytest.raises(type(error)):
        await run_coordinate(case_id=cid, trigger_event_id=event_id, coordinator=FailingCoordinator())
    async with session_scope() as session:
        run = (await session.execute(select(OrchestrationRunModel).where(
            OrchestrationRunModel.case_id == cid))).scalars().one()
        assert run.state == 'FAILED'
        assert run.error_code == expected
        assert 'private' not in str(run.tool_calls)
        assert run.policy_result is None


@pytest.mark.asyncio
async def test_dispatcher_records_safe_validator_code(app_db, monkeypatch):
    from pydantic_ai.exceptions import UnexpectedModelBehavior

    await _assert_dispatcher_failure_code(monkeypatch, UnexpectedModelBehavior('private provider response'),
        'LAST_OBSERVED_VALIDATION_REDUNDANT_TRIAGE')


@pytest.mark.asyncio
async def test_dispatcher_preserves_timeout_class_after_earlier_retry(app_db, monkeypatch):
    await _assert_dispatcher_failure_code(monkeypatch, TimeoutError('private provider response'), 'TimeoutError')


@pytest.mark.asyncio
async def test_real_retry_exhaustion_labels_only_last_observed_validation():
    from pydantic_ai import Agent, ModelRetry, capture_run_messages
    from pydantic_ai.exceptions import UnexpectedModelBehavior
    from pydantic_ai.models.function import FunctionModel
    from app.agents.tracing import validator_failure_code

    def respond(messages, info):
        from pydantic_ai.messages import TextPart
        return ModelResponse(parts=[TextPart('invalid proposal')])

    agent = Agent(FunctionModel(respond), output_type=str, retries=1)
    failures = iter(['Work orders already exist.', 'Critical safety answers are still UNKNOWN.'])

    @agent.output_validator
    def reject(output: str) -> str:
        raise ModelRetry(next(failures))

    with capture_run_messages() as messages:
        with pytest.raises(UnexpectedModelBehavior):
            await agent.run('Offline validation regression')
    # Pydantic raises retry exhaustion before recording the second rejection.
    # The persisted code must describe captured evidence, not assert the final cause.
    assert validator_failure_code(messages) == 'LAST_OBSERVED_VALIDATION_REDUNDANT_TRIAGE'
