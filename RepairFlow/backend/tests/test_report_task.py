import json

import httpx2
import pytest

from app.agents.report_task import ReportInput, ReportTask
from app.agents.mubit import MubitBudgetExceeded
from app.config import Settings


def settings(tmp_path, **kwargs):
    return Settings(_env_file=None, mubit_api_key='test', data_dir=tmp_path,
                    mubit_budget_path=tmp_path / 'budget.db', **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize('split,record', [('train', 'full'), ('dev', 'off'), ('eval', 'off')])
async def test_gateway_contract(tmp_path, split, record):
    requests = []
    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert request.headers['x-middleware-record'] == record
        assert body['max_tokens'] == 256
        assert [t['name'] for t in body['tools']] == ['report_decision']
        prompt = json.loads(body['messages'][0]['content'][0]['text'])
        assert prompt == {'work_scope': 'Repair tap', 'report_text': 'Tap repaired and tested.'}
        return httpx2.Response(200, headers={'x-middleware-request-id': 'req_mock'}, json={
            'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-4-5',
            'content': [{'type': 'tool_use', 'id': 'tool_1', 'name': 'report_decision',
                         'input': {'classification': 'COMPLETED'}}],
            'stop_reason': 'tool_use', 'stop_sequence': None,
            'usage': {'input_tokens': 30, 'output_tokens': 10}})
    task = ReportTask(settings(tmp_path), http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    try:
        output, metrics = await task.infer(ReportInput(work_scope='Repair tap', report_text='Tap repaired and tested.'), split=split)
    finally:
        await task.aclose()
    assert output.classification == 'COMPLETED'
    assert metrics['request_ids'] == ['req_mock']
    assert metrics['requests'] == 1 and metrics['input_tokens'] == 30
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_budget_stops_before_network(tmp_path):
    def forbidden(request):
        pytest.fail('network forbidden')
    task = ReportTask(settings(tmp_path, mubit_max_runs=0), http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(forbidden)))
    try:
        with pytest.raises(MubitBudgetExceeded):
            await task.infer(ReportInput(work_scope='Tap', report_text='Fixed'), split='dev')
    finally:
        await task.aclose()


def test_input_bound_and_extra_labels_rejected():
    with pytest.raises(ValueError):
        ReportInput(work_scope='x', report_text='x' * 6000)
    with pytest.raises(ValueError):
        ReportInput(work_scope='Tap', report_text='Fixed', expected='COMPLETED')


def test_cli_bounds():
    from scripts.train_report_task import parse_args
    assert not parse_args([]).live
    for argv in (['--limit', '65'], ['--offset', '-1'], ['--max-runs', '1001']):
        with pytest.raises(SystemExit):
            parse_args(argv)


@pytest.mark.asyncio
async def test_provider_failure_metrics_no_fallback(tmp_path):
    from pydantic_ai.exceptions import ModelHTTPError
    count = 0
    def respond(request):
        nonlocal count
        count += 1
        return httpx2.Response(500, headers={'x-middleware-request-id': 'req_failure'},
                              json={'type': 'error', 'error': {'type': 'api_error', 'message': 'test error'}})
    task = ReportTask(settings(tmp_path), http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    try:
        with pytest.raises(ModelHTTPError):
            await task.infer(ReportInput(work_scope='Tap', report_text='Repaired'), split='dev')
    finally:
        await task.aclose()
    assert count == 1
    assert task.last_metrics['request_ids'] == ['req_failure']
    assert task.last_metrics['status'] == 'error'


@pytest.mark.asyncio
async def test_runner_stops_after_three_errors(tmp_path, monkeypatch):
    import sys
    import types
    from types import SimpleNamespace
    from scripts import train_report_task as runner
    cases = [SimpleNamespace(key=str(i), split='dev', scope='Tap', report='Fixed', expected='COMPLETED') for i in range(7)]
    monkeypatch.setitem(sys.modules, 'app.report_training_cases', types.SimpleNamespace(scenarios=lambda: cases))
    class FailedTask:
        last_metrics = {'requests': 1}
        def __init__(self, settings):
            pass
        async def infer(self, *args, **kwargs):
            raise RuntimeError('test')
        async def aclose(self):
            pass
    monkeypatch.setattr(runner, 'ReportTask', FailedTask)
    monkeypatch.setattr(runner, 'Settings', lambda: settings(tmp_path))
    args = runner.parse_args(['--live', '--output-dir', str(tmp_path / 'run')])
    result = await runner.run(args)
    assert result['attempted'] == 3 and result['errors'] == 3


@pytest.mark.asyncio
async def test_invalid_classification_cannot_loop_forever(tmp_path):
    count = 0
    def respond(request):
        nonlocal count
        count += 1
        return httpx2.Response(200, json={
            'id': 'msg_test', 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-4-5',
            'content': [{'type': 'tool_use', 'id': f'tool_{count}', 'name': 'report_decision',
                         'input': {'classification': 'UNKNOWN'}}],
            'stop_reason': 'tool_use', 'stop_sequence': None,
            'usage': {'input_tokens': 30, 'output_tokens': 10}})
    task = ReportTask(settings(tmp_path), http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    from pydantic_ai.exceptions import UnexpectedModelBehavior
    try:
        with pytest.raises(UnexpectedModelBehavior):
            await task.infer(ReportInput(work_scope='Tap', report_text='Fixed'))
    finally:
        await task.aclose()
    assert count == 2
