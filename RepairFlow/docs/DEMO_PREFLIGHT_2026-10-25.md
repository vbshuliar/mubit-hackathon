# Demo preflight — 25 October 2026

No screen recording was started during this preflight.

## Current, verified entry point

Use the built current frontend served by the existing backend:
`http://localhost:8000/maintenance`.

Current simulated roof case #100:
`http://localhost:8000/maintenance/tickets/a9c1d4f9-f513-4660-8bfc-348e531914e4`.

The old `449a43a3-a1c5-410a-bb47-3345694c12c2` case was superseded during
fixture recreation. Historical #102 UUIDs in earlier demo guides do not exist
in this local database. Do not navigate using those old links. Earlier footage
is superseded and must not be reused for the final demo.

Earlier loading failures occurred while the backend was stopped for recreation
and while the browser used a superseded case ID. Keep the service and database
unchanged throughout the next recording. Do not recreate data during capture.

Run `./check-demo.ps1` from the repository root before opening the demo. It reads
the current UUID from preparation metadata, checks fixture readiness, case and
action results, and all nine page shells. It is read-only and never records.
HTTP success is only a prerequisite: inspect each rendered screen too.

## Browser rehearsal completed

- Maintenance queue → current #100 link → Overview: resolved case and tenant response.
- Summary: all four simulated contractor reports, including unsafe ladder access
  requiring a scaffold, scaffold handover, repaired roof, and scaffold removal.
- Work: three completed work orders and two satisfied dependency edges.
- Agent: 11 rounds; prerequisite decision expands; execution results succeeded;
  final tenant confirmation and resolution are present.
- Timeline: approvals, completion, response request, tenant response and closure.
- Property: fictional property/tenant data and disabled external contact.
- Files: intentional empty attachment list, with fixture evidence provenance.
- Costs: £475 quoted, £0 invoiced; no invented invoices.
- Messages: intentional empty chat history; authoritative simulated responses
  are recorded in events/reports, not fabricated chat messages.
- Direct page reload works. No browser console errors were returned.

After rebuilding, Overview/Summary/Work/Agent were checked again and the
corrected admission labels were visibly verified. Very rapid scripted tab
clicks sometimes did not navigate; normal native tab clicks worked. During
capture, use native clicks, inspect the URL and content after every transition,
and do not treat a click or an HTML shell as proof that the next screen loaded.

## Repairs and checks

The fixture preparation script now consumes its own queued work, handles
auto-approved roof report acceptance, detects existing cases safely, and keeps
the live UUID in metadata. An isolated 99-case baseline replay completed with
11 successful actions and no WAIT artifacts or pending jobs. The live case was
not restored or rewritten during this preflight. All live case jobs are DONE.

Fixed the frontend admission display: `policy_result=PENDING` is an admission
snapshot, not a statement that application checks remain pending. A successful
admission now displays **Admitted**, while the separate action ledger still
reports **Succeeded**. Applied to summary and decision history. Focused tests
13/13, TypeScript, changed-file ESLint, diff checks and production build passed.
Backend hero-path and simulated-input tests also passed: 39 tests in 6.95s,
using isolated test databases.

## Mubit rehearsal

Authenticated Overview and Evaluations loaded at
`https://app.mubit.ai/console/projects/ws-9ea386dc56aefa33/adapters/ad_lane_89d7129e`.
Verified Qwen3-4B-Instruct-2507, Testing, 91.7% on 12 scored cases, 85% target,
row 11 failed, and readiness requirement of 20 judged cases versus 12 available.
No linked request path. This adapter is not serving the fixture workflow.

## Recording boundaries

This is an already-completed, accelerated simulation walkthrough. Fixture visit
slots may show 27 October even though simulated completion was submitted on
25 October. These are mock appointment dates, not evidence of real attendance.
Do not imply live model reasoning, real messages, or real contractor bookings.
No new paid generation or recording was performed in this preflight.

Next capture must be a fresh recording after a final visible check of each
shot. Confirm the selected native Edge window matches the intended tab; a
background tab's DOM can be correct while the captured foreground is different.
Keep the browser free of the debugging banner, crop account identity from Mubit,
and wait for the user's instruction to start recording.

## Presentation view

The opt-in ?presentation=1 view persists in sessionStorage for the tab. It removes fixture/provenance labels and known fixture wording from the queue and case presentation, while preserving raw API records, mutation values, action outcomes and failures. Browser-verified queue and all case tabs; focused tests, TypeScript and production build passed. It does not imply that real contractor contact occurred or that the trained adapter served this case. No recording started.
