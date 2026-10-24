# Training status and comparison gate — 24 October 2026

## Observed in the authenticated console

- Workspace: `ws-f7685debbc87c0ad`.
- Older task `ln_1671a75b313fb646a60aa1be`: 111 calls, 78 kept, 33 rejected; Training v1, started approximately eight hours before inspection.
- Training job: `ftjob_4061a42b`. No live route, measured regression, or completed match score shown.
- Current task `ln_a84cb308a18c24ae646e3936`: 263 calls initially, 267 at the later tasks-view check; reviewing, 11/25 kept.
- Tasks view: Live 0. A queued/reviewing/training status is not evidence of a working trained model or measured savings.

## Diagnostic prepared for Mubit support (not sent)

Please check job `ftjob_4061a42b` in the workspace and older task above. The console has displayed Training v1 for approximately eight hours and exposes no failure reason or retry control. Is the job queued, running, or stalled? Is there a capacity or workspace limit? What action, if any, is needed to complete training? Please also clarify whether this older task's adapter is compatible with our current versioned prompt and tool contract before routing production requests to it.

## Comparison prepared; blocked until a compatible adapter is available

40 held-out cases were built locally without live calls or recording:

- 18 lifecycle: `backend/data/mubit-collections/20261024T130807-76264d8f`
- 16 legacy: `backend/data/mubit-collections/20261024T131124-6569f678`
- 6 safety: `backend/data/mubit-collections/20261024T131126-258c2b89`

Keep these cases out of training. Use identical frozen inputs, tool results, policy and prompt version for teacher and adapter. Pin and record actual model/adapter IDs, route and fallback; a teacher fallback is not a small-model success. Compare correct action and arguments, policy rejection, safety failures, completion, latency, and actual billed cost where available. Preserve failed attempts in the denominator. Token counts alone do not establish cost savings. Evaluate on copies, never mutate the operational demo database. Start with a small paid smoke comparison before committing the remaining allowance to all 40 pairs.

Official guide: https://docs.mubit.ai/guides/first-adapter . Its comparison flow requires a passed adapter. No trained-model accuracy or percentage-complete claim is currently supported.

## Failure follow-up

- Equipment-blocked visits can no longer be accepted as FAILED merely to add scaffolding later; accepting would consume the report. Both FAILED and NO_ACCESS are guarded, with clarification/prerequisite/escalation available.
- Two missing-safety runs failed without retained proposals. Their exact model output is unavailable; do not attribute a specific unsafe action to them.
- One missing-safety run asked all six questions via OPERATOR instead of TENANT. Preserve the benchmark failure while distinguishing indirect routing from missing safety coverage.
- A fresh live rehearsal found repeat triage after initial work creation. The existing guard blocked it. Prompt v8 now explicitly prioritizes current work-order state over historical intake events. Independent review approved it; the live replay then correctly fetched and scheduled a slot.

Validation after these changes: 406 backend tests passed. Backend restarted with the updated guard and prompt. The ignored local environment cap is 180 decision reservations, not a dollar budget; failed decisions also consume reservations. No billing settings were changed.

## Live rehearsal evidence

Case #103: explicit safety answers → triage → initial booking → completed contractor report → confirmation request → tenant disputes resolution → follow-up work and approval → second booking → completed follow-up report → second confirmation request. The follow-up decision and first closure attempt each exhausted the per-run request/tool allowance; bounded retries via explicit tenant updates succeeded. The case finished RESOLVED at version 20; screenshot: `demo-evidence/recovery-final-resolved.png`. This remains a reliability limitation, not a flawless first-attempt pass. No limits were removed to hide it.

Case #102 was re-inspected in the browser, not replayed with fresh paid decisions: roofing repair, scaffold installation and removal are all completed, dependencies satisfied, and the case resolved. Screenshot: `demo-evidence/scaffold-final-review.png`.

Database checks: original workspace still has 2,474 rows; both original and demo databases pass integrity and foreign-key checks. Final rehearsal ledger reading: 159/180 reservations, leaving 21. These are decision counts, not gateway-request counts or dollar amounts.
