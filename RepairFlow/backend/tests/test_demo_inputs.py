"""Offline text-demo contracts; real policy/executor covered by hero/reliability suites."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.db import session_scope
from app.domain import services
from app.domain.services import ActorContext
from app.models import CommunicationModel, JobModel, RepairCaseModel, ContractorReportModel
from app.schemas import RequestInformation
from tests.test_hero_path import _seed_reference_data
from tests.test_fixi_ui_support import _drive_case_to_scheduled


def body(kind="TENANT_REPLY", **kwargs):
    return {"input_id": str(uuid.uuid4()), "expected_case_version": 1, "kind": kind,
            "text": "The repair issue is still present in the kitchen.", **kwargs}


async def create(client):
    prop, tenant, _, _ = await _seed_reference_data()
    r = await client.post('/api/v1/cases', json={"property_id": prop, "tenant_id": tenant,
        "description": "Kitchen sink is leaking", "location": "Kitchen", "source_text": "My sink is leaking", "simulated": True})
    assert r.status_code == 201, r.text
    return r.json()['case_id']


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['TENANT_REPLY', 'OPERATOR_UPDATE'])
async def test_text_is_model_visible_once_and_requests_close(app_db, kind):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        case_id = await create(client)
        async with session_scope() as session:
            await services.request_information(session, case_id=case_id,
                action=RequestInformation(recipient="OPERATOR" if kind == 'OPERATOR_UPDATE' else "TENANT", purpose="INTAKE", questions=['Where is the leak?']),
                actor=ActorContext('SYSTEM', 'test', str(uuid.uuid4())))
        payload = body(kind)
        url = f'/api/v1/cases/{case_id}/demo-inputs'
        response = await client.post(url, json=payload)
        assert response.status_code == 202, response.text
        assert response.json()['result']['case_version'] == 2
        duplicate = await client.post(url, json=payload)
        assert duplicate.json()['result']['status'] == 'NOOP'
        mismatch = await client.post(url, json={**payload, 'text': 'Changed response'})
        assert mismatch.status_code == 409
        async with session_scope() as session:
            snapshot = await services.load_case_snapshot(session, case_id)
            assert snapshot.issue.evidence_refs[0].provenance == 'SIMULATED'
            assert any(t.text == payload['text'] for c in snapshot.communications for t in c.transcript)
            assert not any(c.state == 'REQUESTED' for c in snapshot.communications)
            jobs = (await session.execute(select(JobModel).where(JobModel.case_id == case_id))).scalars().all()
            assert len(jobs) == 2  # intake + one response wake
            assert all(j.kind == 'COORDINATE' for j in jobs)


@pytest.mark.asyncio
async def test_safety_availability_provenance_and_stale_guard(app_db):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid = await create(client)
        start = datetime.now(timezone.utc) + timedelta(days=1)
        response = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=body(safety_answers={'gas': 'YES'}, availability=[{
            'start_at':start.isoformat(), 'end_at':(start+timedelta(hours=5)).isoformat(), 'timezone':'Europe/London',
            'spoken_text':'Tomorrow afternoon', 'confirmed_by_speaker':True}]))
        assert response.status_code == 202, response.text
        async with session_scope() as session:
            snap = await services.load_case_snapshot(session,cid)
            assert snap.case.risk.gas == 'YES'
            assert snap.availability[0].source_ref.provenance == 'SIMULATED'
        stale = await client.post(f'/api/v1/cases/{cid}/demo-inputs', json=body())
        assert stale.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['RESOLVED','CANCELLED'])
async def test_terminal_input_rejected(app_db,status):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid=await create(client)
        async with session_scope() as session:
            case=await session.get(RepairCaseModel,cid);case.status=status
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body())
        assert r.status_code==409


@pytest.mark.asyncio
@pytest.mark.parametrize('confirmed', [True,False])
async def test_confirmation_is_evidence_not_direct_closure(app_db,confirmed):
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        cid=await create(client)
        payload=body('TENANT_CONFIRMATION',confirms_resolved=confirmed)
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=payload)
        assert r.status_code==409
        async with session_scope() as session:
            case=await session.get(RepairCaseModel,cid);case.status='AWAITING_CONFIRMATION'
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=payload)
        assert r.status_code==202,r.text
        async with session_scope() as session:
            snap=await services.load_case_snapshot(session,cid)
            assert snap.case.status==('AWAITING_CONFIRMATION' if confirmed else 'ACTIVE')
            assert bool(snap.issue.tenant_resolution_confirmed_at)==confirmed


@pytest.mark.asyncio
@pytest.mark.parametrize('kind,outcome', [('CONTRACTOR_REPORT',None),('ATTENDANCE_OUTCOME','NO_ACCESS'),('ATTENDANCE_OUTCOME','NO_SHOW'),('ATTENDANCE_OUTCOME','AWAITING_REPORT')])
async def test_visit_evidence_does_not_complete_work(app_db,kind,outcome):
    prop,tenant,roofer,_=await _seed_reference_data()
    cid,_,work,appointment=await _drive_case_to_scheduled(prop,tenant,roofer)
    async with session_scope() as session:
        version=(await services.load_case(session,cid)).version
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        payload=body(kind,expected_case_version=version,appointment_id=appointment.id)
        if outcome:payload['attendance_outcome']=outcome
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=payload)
        assert r.status_code==202,r.text
        async with session_scope() as session:
            snap=await services.load_case_snapshot(session,cid)
            assert snap.work_orders[0].status=='AWAITING_REPORT'
            assert snap.case.status!='RESOLVED'
            if outcome!='AWAITING_REPORT':
                assert snap.latest_reports[0].provenance=='SIMULATED'
                assert snap.latest_reports[0].interpretation_status=='PENDING'
            assert snap.snapshot_version==version+1


@pytest.mark.asyncio
async def test_cross_case_appointment_rejected(app_db):
    prop,tenant,roofer,_=await _seed_reference_data()
    cid,_,_,appointment=await _drive_case_to_scheduled(prop,tenant,roofer)
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        other=await create(client)
        r=await client.post(f'/api/v1/cases/{other}/demo-inputs',json=body('CONTRACTOR_REPORT',appointment_id=appointment.id))
        assert r.status_code==404,r.text


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [body(text=' '),body('CONTRACTOR_REPORT'),body('TENANT_CONFIRMATION'),body('ATTENDANCE_OUTCOME'),body('AVAILABILITY'),body(appointment_id=str(uuid.uuid4()))])
async def test_invalid_input_shapes_rejected(app_db,payload):
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=payload)
        assert r.status_code==422,r.text


@pytest.mark.asyncio
async def test_calling_endpoints_removed(app_db):
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        for path in ['/api/v1/voice/session','/api/v1/communications/123/recording','/api/v1/communications/123/retry-recording','/integrations/elevenlabs/webhook']:
            r=await client.post(path,json={}) if 'recording' not in path or 'retry' in path else await client.get(path)
            assert r.status_code in (404,405)


@pytest.mark.asyncio
async def test_legacy_outreach_jobs_fail_closed(app_db):
    from app.orchestration.worker import drain_due_jobs
    from app.orchestration.dispatcher import FixtureCoordinator
    async with session_scope() as session:
        for kind in ('PLACE_CALL','FETCH_RECORDING'):
            await services.enqueue_job(session,case_id=None,kind=kind,dedupe_key=str(uuid.uuid4()),payload={})
    assert await drain_due_jobs(FixtureCoordinator(),raise_on_error=True)==2
    async with session_scope() as session:
        jobs=(await session.execute(select(JobModel))).scalars().all()
        assert all(j.status=='FAILED' and 'removed' in j.last_error for j in jobs)


@pytest.mark.asyncio
async def test_missing_report_response_closes_report_request_not_tenant_request(app_db):
    prop,tenant,roofer,_=await _seed_reference_data()
    cid,_,_,appointment=await _drive_case_to_scheduled(prop,tenant,roofer)
    async with session_scope() as session:
        version=(await services.load_case(session,cid)).version
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        url=f'/api/v1/cases/{cid}/demo-inputs'
        r=await client.post(url,json=body('ATTENDANCE_OUTCOME',expected_case_version=version,
            appointment_id=appointment.id,attendance_outcome='AWAITING_REPORT'))
        assert r.status_code==202,r.text
        async with session_scope() as session:
            for recipient,purpose in [('OPERATOR','CONTRACTOR'),('TENANT','AVAILABILITY')]:
                await services.request_information(session,case_id=cid,
                    action=RequestInformation(recipient=recipient,purpose=purpose,questions=['Please provide details']),
                    actor=ActorContext('SYSTEM','test',str(uuid.uuid4())))
        r=await client.post(url,json=body('CONTRACTOR_REPORT',expected_case_version=version+1,
            appointment_id=appointment.id,text='Repaired leak and tested sink successfully.'))
        assert r.status_code==202,r.text
        async with session_scope() as session:
            snap=await services.load_case_snapshot(session,cid)
            assert not any(c.state=='REQUESTED' and c.purpose=='CONTRACTOR' for c in snap.communications)
            assert any(c.state=='REQUESTED' and c.purpose=='AVAILABILITY' for c in snap.communications)


@pytest.mark.asyncio
@pytest.mark.parametrize('change', [
    {'confirmed_by_speaker':False}, {'timezone':'Not/AZone'},
    {'start_at':'2026-10-25T12:00:00','end_at':'2026-10-25T13:00:00'},
    {'start_at':'2099-01-03T12:00:00Z','end_at':'2099-01-02T12:00:00Z'},
])
async def test_intake_rejects_invalid_availability(app_db,change):
    prop,tenant,_,_=await _seed_reference_data()
    window={'start_at':'2099-01-02T12:00:00Z','end_at':'2099-01-02T13:00:00Z',
        'timezone':'Europe/London','spoken_text':'Tomorrow','confirmed_by_speaker':True,**change}
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        r=await client.post('/api/v1/cases',json={'property_id':prop,'tenant_id':tenant,
            'description':'Sink leak in the kitchen','location':'Kitchen','source_text':'My sink leaks','availability':[window]})
        assert r.status_code==422,r.text


@pytest.mark.asyncio
async def test_concurrent_inputs_cannot_overwrite_same_version(app_db):
    import asyncio
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
        results=await asyncio.gather(*[client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body(text=f'New response {i}')) for i in range(2)])
        assert sorted(r.status_code for r in results)==[202,409]


@pytest.mark.asyncio
async def test_model_cannot_invent_negative_safety_answers_and_rejection_is_terminal(app_db):
    from app.orchestration.dispatcher import FixtureCoordinator
    from app.orchestration.worker import drain_due_jobs
    from app.models import OrchestrationRunModel
    from app.schemas import ActionProposal, ApplyTriage, RiskAssessment

    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)  # all safety answers deliberately UNKNOWN
    async def unsafe(snapshot, trigger_event_id):
        return ActionProposal(case_id=cid, expected_case_version=snapshot.snapshot_version,
            trigger_event_id=trigger_event_id,decision_summary='Incorrectly guessing safety',evidence_refs=[],
            action=ApplyTriage(risk=RiskAssessment(gas='NO',fire='NO',water_near_electrics='NO',
                structural_danger='NO',uncontrolled_flood='NO',vulnerability_concern='NO'),
                issue_description='Kitchen leak',suggested_trade='PLUMBING',scope='Fix sink'))
    coordinator=FixtureCoordinator([unsafe])
    assert await drain_due_jobs(coordinator,raise_on_error=True)==1
    async with session_scope() as session:
        snap=await services.load_case_snapshot(session,cid)
        assert snap.case.risk.gas=='UNKNOWN'
        assert not snap.work_orders
        assert not snap.agent_active
        runs=(await session.execute(select(OrchestrationRunModel))).scalars().all()
        assert len(runs)==1 and runs[0].state=='FAILED'
        assert 'not confirmed NO' in runs[0].policy_result
        assert runs[0].proposal['action']['kind']=='APPLY_TRIAGE'


@pytest.mark.asyncio
async def test_future_followup_is_waiting_not_agent_active(app_db):
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
    async with session_scope() as session:
        jobs=(await session.execute(select(JobModel))).scalars().all()
        for job in jobs:job.status='DONE'
        await services.enqueue_job(session,case_id=cid,kind='FOLLOW_UP',dedupe_key=str(uuid.uuid4()),payload={},
            run_at=datetime.now(timezone.utc)+timedelta(days=1))
    async with session_scope() as session:
        assert not (await services.load_case_snapshot(session,cid)).agent_active


@pytest.mark.asyncio
async def test_explicit_reply_closes_only_selected_request(app_db):
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
        ids={}
        async with session_scope() as session:
            for purpose in ('INTAKE','AVAILABILITY','FOLLOW_UP'):
                result=await services.request_information(session,case_id=cid,
                    action=RequestInformation(recipient='TENANT',purpose=purpose,questions=['Please provide details']),
                    confirmation_request=(purpose == 'FOLLOW_UP'),
                    actor=ActorContext('SYSTEM','test',str(uuid.uuid4())))
                ids[purpose]=str(result.resource_ids['communication_id'])
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body(response_to_communication_id=ids['FOLLOW_UP']))
        assert r.status_code==409
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body(response_to_communication_id=ids['INTAKE']))
        assert r.status_code==202,r.text
        async with session_scope() as session:
            assert (await session.get(CommunicationModel,ids['INTAKE'])).state=='ENDED'
            assert (await session.get(CommunicationModel,ids['AVAILABILITY'])).state=='REQUESTED'
            assert (await session.get(CommunicationModel,ids['FOLLOW_UP'])).state=='REQUESTED'


def test_model_cannot_remove_recorded_vulnerability_review():
    from app.domain.policy import validate_triage_evidence
    from app.domain.errors import PolicyRejectedError
    from app.schemas import RiskAssessment
    known = dict(gas='NO',fire='NO',water_near_electrics='NO',structural_danger='NO',uncontrolled_flood='NO')
    with pytest.raises(PolicyRejectedError,match='cannot be downgraded'):
        validate_triage_evidence(RiskAssessment(**known,vulnerability_concern='YES'),
                                 RiskAssessment(**known,vulnerability_concern='UNKNOWN'))


@pytest.mark.asyncio
async def test_runs_expose_executor_failure_and_wrong_coverage_is_rejected(app_db):
    from app.models import ContractorModel
    from app.schemas import ActionProposal, ScheduleVisit, AppointmentQuery
    from app.orchestration.dispatcher import FixtureCoordinator, run_coordinate
    from app.orchestration.executor import execute_action
    from app.integrations.booking import mock_booking_connector
    prop,tenant,roofer,_=await _seed_reference_data()
    cid,_,work,appointment=await _drive_case_to_scheduled(prop,tenant,roofer)
    async with session_scope() as session:
        result=await services.cancel_appointment(session,appointment_id=appointment.id,
            reason='New date required',actor=ActorContext('OPERATOR','test',str(uuid.uuid4())))
        contractor=await session.get(ContractorModel,roofer)
        contractor.service_postcodes=['BS4','BS5']
    async with session_scope() as session:
        snap=await services.load_case_snapshot(session,cid)
        assert not await mock_booking_connector.list_slots(session,
            AppointmentQuery(case_id=cid,work_order_id=work.id,contractor_id=roofer,tenant_availability_ids=[]),trade=work.trade)
    proposal=ActionProposal(case_id=cid,expected_case_version=snap.snapshot_version,trigger_event_id=snap.recent_events[-1].id,
        decision_summary='Wrong contractor coverage',evidence_refs=[],action=ScheduleVisit(work_order_id=work.id,
        contractor_id=roofer,slot_id=appointment.slot_id,tenant_availability_ids=[w.id for w in snap.availability]))
    admitted=await run_coordinate(case_id=cid,trigger_event_id=str(snap.recent_events[-1].id),coordinator=FixtureCoordinator([proposal]))
    await execute_action(admitted.id)
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        r=await client.get(f'/api/v1/cases/{cid}/runs')
        latest=r.json()['items'][0]
        assert latest['state']=='SUCCEEDED'
        assert latest['action_state']=='FAILED'
        assert 'postcode' in latest['action_error']


@pytest.mark.parametrize('codes,postcode,expected', [(['BS1'],'BS1 1AA',True),(['BS1'],'BS10 2AA',False),
    (['BS4','BS5'],'BS1 1AA',False),(['BS1'],'BS11AA',True),([],'BS1 1AA',False)])
def test_contractor_postcodes_require_explicit_match(codes,postcode,expected):
    from app.domain.policy import contractor_covers_postcode
    assert contractor_covers_postcode(codes,postcode)==expected


@pytest.mark.asyncio
async def test_resolution_requires_real_confirmation_event_and_ingress_is_simulated(app_db):
    from app.schemas import ResolveCase
    from app.domain.errors import PolicyRejectedError
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
        async with session_scope() as session:
            case=await session.get(RepairCaseModel,cid)
            case.status='AWAITING_CONFIRMATION'
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body('TENANT_CONFIRMATION',confirms_resolved=True))
        assert r.status_code==202,r.text
        async with session_scope() as session:
            snap=await services.load_case_snapshot(session,cid)
            confirmation=next(e for e in snap.recent_events if e.type=='TENANT_CONFIRMATION_RECEIVED')
            assert confirmation.provenance=='SIMULATED'
            assert next(e for e in snap.recent_events if e.type=='CASE_CREATED').provenance=='SIMULATED'
            with pytest.raises(PolicyRejectedError,match='latest affirmative'):
                await services.resolve_case(session,case_id=cid,
                    action=ResolveCase(issue_id=snap.issue.id,confirmation_event_id=uuid.uuid4()),
                    trigger_event_id=str(confirmation.id),actor=ActorContext('EXECUTOR','test',str(uuid.uuid4())))
            result=await services.resolve_case(session,case_id=cid,
                action=ResolveCase(issue_id=snap.issue.id,confirmation_event_id=confirmation.id),
                trigger_event_id=str(confirmation.id),actor=ActorContext('EXECUTOR','test',str(uuid.uuid4())))
            assert result.status=='APPLIED'


@pytest.mark.asyncio
async def test_reply_availability_and_safety_event_provenance(app_db):
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        cid=await create(client)
        start=datetime.now(timezone.utc)+timedelta(days=2)
        r=await client.post(f'/api/v1/cases/{cid}/demo-inputs',json=body(safety_answers={'gas':'NO'},availability=[{
            'start_at':start.isoformat(),'end_at':(start+timedelta(hours=3)).isoformat(),
            'timezone':'Europe/London','spoken_text':'Available afternoon','confirmed_by_speaker':True}]))
        assert r.status_code==202,r.text
        async with session_scope() as session:
            snap=await services.load_case_snapshot(session,cid)
            assert all(e.provenance=='SIMULATED' for e in snap.recent_events)
            assert snap.case.risk.evidence_refs[-1].provenance=='SIMULATED'
            assert str(snap.case.risk.evidence_refs[-1].source_id)!=str(snap.case.risk.evidence_refs[0].source_id)
