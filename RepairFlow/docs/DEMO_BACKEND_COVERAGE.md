# Backend demo coverage — 24 October 2026

## What the tests establish

The default backend suite is offline. It runs against temporary databases and fake
provider transports or Pydantic AI `FunctionModel` responses. It exercises real
validation, tools, domain commands, policy, executor, worker and API serialization.
It does **not** establish that a live language model will always choose the right
action, that Mubit has trained an adapter, or that all unseen reports are covered.
Live browser outcomes are recorded separately in the final demo verification report.

Run from `backend/` with `uv run pytest -q`. The test environment ignores the local
secret-bearing `.env` and uses separate database/storage directories.

## Supported flow and guard matrix

| Area | Evidence exercised | Main test files |
| --- | --- | --- |
| Text intake | Case creation, source text, SIMULATED issue/risk references; intake idempotency | `test_demo_inputs.py`, `test_api.py`, `test_audit_regressions.py` |
| Human replies | Tenant/operator free text reaches snapshot; one version increment/wake; matching request closes; ingress events and updated safety source references preserve provenance | `test_demo_inputs.py` |
| Request association | Explicit response closes only selected request; cannot substitute ordinary reply for resolution confirmation | `test_demo_inputs.py` |
| Availability | Confirmed future timezone-aware windows; invalid zone, reversed dates and unconfirmed intake rejected | `test_demo_inputs.py` |
| Integrity | Wrong-case appointment, stale version, terminal case, changed-content idempotency conflict, concurrent same-version submissions | `test_demo_inputs.py` |
| Contractor report | Correct visit/work linkage, SIMULATED report; submission does not complete work | `test_demo_inputs.py`, `test_hero_path.py` |
| Missing report | Window-ended evidence → request → report closes report request without closing tenant question | `test_demo_inputs.py` |
| No access/no show | Evidence enters normal report interpretation; work remains incomplete | `test_demo_inputs.py`, `test_reliability_matrix.py` |
| Tenant confirmation | Explicit true/false, accepted only at confirmation stage; positive evidence alone does not close case; closure requires the latest real affirmative event ID in this case | `test_demo_inputs.py`, `test_hero_path.py` |
| Prerequisite work | Roofing → scaffold installation → resumed repair → removal/confirmation; approvals, dependency ordering, duplicate/restart behavior | `test_hero_path.py`, `test_phase2_reliability.py`, `test_reliability_matrix.py` |
| Safety | Model cannot invent NO from UNKNOWN or remove recorded YES/vulnerability; hazard gate precedes inference | `test_demo_inputs.py`, `test_coordinator.py`, `test_audit_regressions.py` |
| Scheduling tools | Invented slot corrected in same Pydantic run; actual returned tuple and covering availability required; repeated invalid output stops | `test_coordinator.py` |
| Supplier eligibility | Required trade and explicit postcode coverage; BS1 does not accidentally match BS10 | `test_demo_inputs.py`, `test_audit_regressions.py` |
| Closure workflow | Resolve/confirmation shortcuts rejected before final output; prerequisite interpretation remains permitted; already applied reports cannot be reinterpreted | `test_coordinator.py` |
| Research | Fixture result preserved, candidate status unverified, bounded adapter failure behavior, one versioned wake on completion, normal executor path | `test_research.py` |
| Runtime failures | Policy rejection and token exhaustion persist FAILED, no stranded RUNNING record; no repeat paid run for exhausted validation/usage | `test_demo_inputs.py`, `test_coordinator.py`, `test_correctness_batch.py` |
| Observability | Actual read-call traces; model result and corresponding action result shown separately | `test_tracing.py`, `test_demo_inputs.py` |
| Waiting vs working | Future follow-up timer does not mark the coordinator as actively thinking | `test_demo_inputs.py` |
| Cost control | Persistent budget reservation, paused budget, shared ledger and token limits | `test_mubit.py` |
| Prompt size | All supplied human text/reports/risk/work/dependencies/pending actions and event timing retained; irrelevant roster/transport metadata omitted | `test_coordinator.py` |
| Calling removal | Removed routes cannot be invoked; historical calling jobs fail closed | `test_demo_inputs.py` |
| Existing app behavior | Case lists, filters, metrics, documents, costs, approvals, archive isolation, bootstrap/snapshot checks | Remaining backend suites |

## Changes prompted by live failures

The browser checks exposed problems that earlier fake-model tests did not detect:

1. A model inferred negative safety answers from an ordinary-looking repair. A
   deterministic evidence guard now rejects that at model validation and admission.
   Model output must request missing critical safety answers before nonhazard triage;
   retaining UNKNOWN while requesting approval does not bypass this question step.
2. A model invented a timestamp as a slot ID. Scheduling output must now come from
   this run's scoped availability tool, with independent execution checks.
3. A successful model response was mistaken for a successful action. Runs now expose
   `action_state` and `action_error` from the action ledger.
4. Token limits were exhausted after rereading history and exploring irrelevant
   contractors. Compact input preserves evidence while filtering the roster by trade
   and postcode. The 60,000-token guard was not increased.
5. A model researched despite an available approved supplier. Bounded output
   validation now rejects unnecessary discovery. Completed research also creates one
   versioned wake, so it cannot silently leave the workflow idle.
6. A model jumped from a contractor report to closure. Validation now enforces
   readiness for confirmation and actual tenant confirmation before resolution.
7. A model re-accepted an already applied roof report instead of scheduling scaffold
   removal. Only PENDING reports may be interpreted; validation points to remaining
   READY work, and prompt version 7 explicitly requires following that work.

Prompt versions changed as these application corrections were made. Their effects
must not be presented as improvement learned by Mubit. Different prompt/task
fingerprints also mean counts from earlier collection cannot simply be combined.

## Remaining limits

- Fake-model tests verify contracts and selected sequences, not general language
  understanding. New phrasing can still lead to a rejected or escalated proposal.
- The model receives one bounded correction for invalid output. Failure is visible;
  exhausting this correction does not guarantee automatic recovery.
- Booking is a labelled local simulation. It does not contact a contractor or verify
  a real calendar. Human response input is explicitly simulated.
- SQLite is operated with one worker. The input endpoint serializes version checks,
  but this is not a distributed/concurrent-worker deployment certification.
- Held-out Mubit evaluation and a trained adapter require separate live evidence.
  Successful data collection or a console request count alone is insufficient.
- Run/token limits bound activity, not an exact dollar invoice. Actual provider
  billing and model-token accounting remain external facts.
- Historical phone-related fields and files are retained for data compatibility;
  the calling transport and recording retrieval routes are removed.

Final suite after the obsolete-approval rejection regression: **304 passed in 21.25 seconds**. Rejection records one audit event and queues no model wake.
