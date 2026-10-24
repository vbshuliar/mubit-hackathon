# RepairFlow text demo implementation plan

Requested 24 October 2026. Work proceeds without further approval questions.

## Product and limits

Show a real coordinator making repair decisions from simulated human responses.
Keep current FastAPI/SQLite/Pydantic AI and React application. Remove ElevenLabs,
phone dialing, voice sessions, recording retrieval and their UI. Preserve historical
records and the source database; use a separate demo database for browser journeys.
Do not delete unrelated components: produce a proposed declutter list for review.
Mubit improvement is only claimed if its console and measured comparisons support it.
No finite test suite guarantees every unseen case; cover each supported action/wait
and document remaining limits. Total available Mubit credit is $25, not a spending
target. Run offline checks first, stop blind repeated collection, and bound live runs.

## Stage 1 — Inventory and evidence

- [x] Map all waiting states, actions, endpoint contracts and UI entry points.
- [x] Inspect current Mubit task review, adapters, learnings and available usage.
- [x] Record actual status; distinguish received requests, kept examples and training.
- [x] Inventory calling dependencies and historical data compatibility.
- [x] Define shared response API and acceptance matrix before parallel implementation.

## Stage 2 — Replace calling with text inputs

- [x] Delete provider transport, voice/webhook routes, call jobs and recording UI.
- [x] Remove provider settings, dependencies and obsolete tests/scripts.
- [x] Make requests for information/confirmation durable text requests.
- [x] Add case-scoped simulated input: tenant reply, safety answers, availability,
      contractor report, appointment outcome, resolution confirmation and general update.
- [x] Validate IDs against case, current state, input lengths and versions.
- [x] Persist text as evidence; mark simulated provenance; close matching pending requests.
- [x] Wake the coordinator once per accepted input; retain dedupe and safety guards.
- [x] Preserve approvals, escalation/resume and dependency/closure invariants.

## Stage 3 — Demo experience

- [x] Put a prominent response panel on the repair case, beside decision/progress context.
- [x] Show who/what the agent awaits and the actual requested questions.
- [x] Offer contextual input types, appointment selector and explicit structured fields
      when needed; free text remains the primary interaction.
- [x] Show input saved, agent working, chosen action, executed/blocked result and next wait.
- [x] Keep real model tool traces visible; distinguish reasoning from simulated work.
- [x] Ticket creation is text-first and supports demo provenance.
- [x] Explain Mubit plainly without implying an unverified trained model is serving.

## Stage 4 — Offline correctness and budget control

- [x] Add deterministic backend tests for every response kind and waiting/action branch.
- [x] Cover hazards, missing information, contradictory replies, denied approvals,
      unresolved repairs, no report/no access, prerequisite installation/removal,
      invalid or cross-case IDs, duplicate input, stale state, provider failure/retry.
- [x] Test frontend state/input logic; run typecheck, lint, production build and suites.
- [x] Add bounded live-call accounting/guard if current controls cannot protect credit.
- [x] Have independent reviewers inspect backend and frontend changes; resolve findings.

## Stage 5 — Browser journeys and fixes

- [x] Start app against a separate demo database and preserve original data/files.
- [x] Create a new repair ticket through the UI and complete a normal repair.
- [x] Exercise roofing → scaffolding prerequisite → roof repair → tenant confirmation
      and any required scaffold removal, respecting approvals.
- [x] Exercise missing information/availability, hazardous escalation, missing-report
      escalation and recovery in the browser; cover negative replies and missed visits offline.
- [x] Use bounded real Mubit decisions for representative journeys; remaining exhaustive
      branch checks run offline and are labelled as such.
- [x] Inspect screens, logs, database invariants, actual actions and failure handling.
- [x] Fix discovered defects and rerun the affected tests/journeys.

## Stage 6 — Mubit and final evidence

- [x] Recheck Mubit console; record task, kept count, training/adapter/test state.
- [x] If an adapter passed and is available, compare with provider on held-out cases;
      otherwise record the concrete external blocker without claiming savings.
- [x] Save measured latency/token usage and avoid billing estimates presented as facts.
- [x] Produce a demo walkthrough, verification report, and component declutter proposal.
- [x] Reconcile current docs/contracts and leave both servers running.

## Acceptance matrix

| Flow | Expected evidence |
| --- | --- |
| Text intake | Case and issue created, triage decision visible |
| Missing facts | Specific question → simulated reply → agent resumes |
| Availability | Explicit window stored → relevant appointment choice |
| Contractor visit | Report attached to correct appointment → typed next action |
| Prerequisite | Original repair remains open/blocked until dependency satisfied |
| Resolution | Tenant confirmation plus all required work gates closure |
| Unresolved reply | No false closure; further action or explicit escalation |
| Hazard | Deterministic escalation, no unsafe advice or automatic continuation |
| Approval | No commitment before approval; rejection visibly handled |
| Failure | Visible failed run, bounded retries, no silent provider substitution |
| Calling removal | No dialing/session/webhook transport or calling controls remain |
| Budget | Live runs bounded; offline and live results reported separately |

## Progress notes

Initial inspection: existing update dialog only covers reports, tenant confirmation
and ended visit windows. General free text currently does not create meaningful
observations. Pending communication requests and provenance require backend changes.

### Implementation checkpoint

- Backend text response API and calling removal implemented; first full suite 275
  passed. Independent review identified request association and intake-window
  validation issues; fixes and additional tests are in progress.
- Frontend response panel and actual decision summary implemented; 113 tests,
  typecheck and production build passed. Review fixes are in progress.
- Persistent shared paid-run guard implemented and reviewed, including concurrency,
  failed runs, zero-run pause and token-limit tests (11 focused tests passed).
- Browser normal repair #100 exposed a real model safety inference bug and stale
  case-version polling. Both are being fixed before continuing the journey.
- Console refresh reported Engine unreachable, then required sign-in. Adapter
  training cannot currently be confirmed. A no-generation gateway model-list call
  succeeded, so bounded live workflow checks are possible independently.

### Browser checkpoint, 24 October 03:59 BST

- Backend 295 and frontend 138 tests passed before latest display/context refinements.
- Safety escalation #101 passed in the browser with zero model calls.
- Normal repair #100 exposed invented slots; exact tool-returned slot and contractor
  coverage checks now reject those proposals. Recovery hit the 60k-token limit;
  recorded failure persisted correctly, but UI polling missed its final update.
  Context slimming and final-state polling are being corrected before another run.
- Original database still matches all 2,474 snapshot rows and 15 files. Demo database
  integrity is OK with no foreign-key violations.
- Mubit adapter page 03:58 BST: no adapters, 0 kept examples, 25 required. Learnings
  page: none. No adapter comparison or training-success claim is possible yet.


### Final checkpoint

Normal repair #100 and roof/scaffold #102 are resolved through browser-operated,
Mubit-backed decisions. Hazard #101 remains safely escalated; missing-facts #103
requests safety information. Backend 304 and frontend 158 tests passed after the
last rejection-dialog check. Original data is unchanged. Both servers remain running
on the isolated demo workspace. Full outcomes and final checks are in DEMO_VERIFICATION.md.

Stage 6's adapter comparison is conditional and cannot run: the console confirms
zero kept examples/no adapter, with 111 examples waiting review. This external
blocker is documented; no training or savings claim is made and no more blind
collection is authorized by this plan.
