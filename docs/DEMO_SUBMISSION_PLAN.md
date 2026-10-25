# 🎬 Fixi — two-minute demo and submission plan

**Working title:** “The repair is not finished when the message arrives.”

**Audience takeaway:** Fixi coordinates a repair through changing evidence; Mubit has trained a specialist for one recurring decision inside that workflow. The application remains responsible for safe execution.

**Target video length:** 1 minute 50 seconds. The user's maximum is **2 minutes**, leaving ten seconds of margin. This is stricter than the supplied event limit. Deliver an MP4 or MOV plus a separate PDF deck. This is a production plan, not a claim that the video, deck or additional rehearsal has already been completed.

## 1. The story to tell

A roof leak starts as one job. A contractor discovers that scaffolding is needed. A careless system could mistake “visit completed” for “repair completed.” Fixi preserves the unresolved roof work, introduces the prerequisite, and continues only when the required evidence and approvals arrive.

The repeated language task is interpreting the report against its assigned work. That is the focused task sent through Mubit—not the entire repair process compressed into a small model.

**Three proof moments:**

1. The original repair remains unresolved when a prerequisite appears.
2. The UI distinguishes a proposed action from its actual execution result.
3. The Mubit console shows a real trained version and its measured quality, including the remaining readiness gate.

## 2. Choose the honest demo mode before recording

| Mode | When to use it | Required label |
|---|---|---|
| Live provider-backed workflow | Backend healthy, Mubit provider configured, sufficient approved request budget | “Live agent via Mubit · simulated visits and messages.” |
| Recorded verified workflow | External latency, authentication or request budget makes live recording unreliable | “Recorded demo run · simulated physical work.” |
| Fixture workflow | Only if clearly demonstrating software behavior offline | “Deterministic fixture · not live model reasoning.” |
| Live trained adapter | Only after readiness, supported routing and actual version/fallback provenance are verified | Actual adapter/version and observed result. |

At the last verified checkpoint, the trained adapter was **not serving the app**. The default plan therefore combines a provider-backed workflow with a separate console evidence segment. Do not enable a failed version, lower quality requirements, or spend more training credits simply to make the recording look complete.

## 3. Exact storyboard: 1:50 total

| Time | Picture and action | Narration | Evidence to keep visible |
|---|---|---|---|
| 0:00–0:10 | Roof-leak case; brief title overlay | “A roof leak becomes a coordination problem: visits, scaffolding, approvals and confirmation. Fixi keeps that chain moving.” | Original issue; “simulated visits and messages” label. |
| 0:10–0:30 | Contractor report, then prerequisite and action result | “The roofer cannot proceed without scaffolding. The agent creates prerequisite work and keeps the original repair open. Application rules check its proposed actions.” | Report, unresolved roof work, executed action. |
| 0:30–0:48 | Edited progression through handover, roof repair and confirmation | “We enter simulated replies here. Handover unlocks the roof work; the case closes only after the remaining work and tenant confirmation.” | Same case, dependencies and final state. Label time cuts. |
| 0:48–1:05 | Scope + report → Mubit → specialist diagram | “Mubit is our learning layer. We collected recurring report decisions through its gateway to train a specialist for this focused task.” | Seven-outcome contract; separate learning and execution paths. |
| 1:05–1:30 | Second-account adapter evaluation screen | “Mubit trained a Qwen3 four-billion-parameter adapter. It scored eleven out of twelve: 91.7%, above the 85% target. Live readiness still requires twenty judged cases, so it is not powering this workflow yet.” | Model, score, denominator, target and Testing status. |
| 1:30–1:42 | Compact next-steps slide | “Next we verify adapter serving and benchmark unseen cases, latency and cost per correct decision. Savings are a goal, not a measured result yet.” | Readiness → serving → independent benchmark. |
| 1:42–1:50 | Return to case and closing title | “Fixi follows repairs through. Mubit helps the repeated decisions become a specialized model.” | Project name and repository URL. |


This sequence uses edited cuts through one coherent case; it does not imply that multiple physical appointments occur live within two minutes. If completing a new scenario requires excessive calls, use the existing documented case history rather than generating a new run just for footage.

### Editing priorities

Keep the narration near 200 words and time an actual read before export. Show a prepared case instead of typing the full intake. Use edited footage for handover and completion; never wait through several model calls on camera. Omit dashboard tours, the old/new UI comparison, numerical savings scenarios and a second hazard case. Keep those details in the PDF and README. If the cut runs long, shorten transitions—not the adapter readiness disclosure. Final exported duration must be **120 seconds or less**, including titles and ending.

## 4. Operator runbook and sample inputs

Use a synthetic property and tenant from the demo workspace. Choose an actual returned appointment option and future dates supported by the UI. Do not hard-code obsolete slot IDs, invent evidence, or approve an action without reviewing it.

### A. Intake

Suggested scenario text:

> Rain is entering near the bedroom ceiling below the roof flashing. The tenant reports no gas smell, no exposed electrics, no structural movement and no immediate danger. Please investigate and repair the leak. The tenant can provide access during the agreed appointment window.

Enter only the safety answers actually supplied in the scenario. If the UI requires an exact access window, provide one explicitly; the prose above is not a replacement for the booking fields.

### B. Contractor finds a prerequisite

For the booked roof work, submit:

> Defective flashing found. The roof repair could not proceed without scaffolding. Install scaffolding with verified handover before the return visit. The original leak remains unresolved. Scaffolding removal is required after the repair.

**Expected semantic outcome:** roof repair stays open; scaffolding becomes prerequisite work. The exact number of coordinator steps may vary. Show the recorded action rather than predicting a tool name that has not appeared.

### C. Installation and handover

For the appropriate scaffolding appointment, submit:

> Scaffolding installation is complete. The handover inspection is complete and access is ready for the roof contractor. The roof flashing has not been repaired by this visit.

Review any approval request. **Expected outcome:** only the scaffolding scope is completed; roof work can resume when the workflow permits it.

### D. Roof completion

For the correct roof appointment, submit:

> Defective flashing replaced and sealed. Water testing found no further ingress. The assigned roof repair is complete. Scaffolding remains on site and still requires removal.

**Expected outcome:** completion evidence for the roof, with removal still visible if required. Do not hide remaining work to obtain a resolved screen.

### E. Removal and tenant confirmation

Submit a completion report for the removal appointment only after that work exists and is booked. Then use the actual tenant confirmation form and explicitly select the positive response:

> The leak has stopped, the room is dry, and the scaffolding has been removed. I confirm the repair is complete.

**Expected outcome:** case resolution only after required work and confirmation gates pass. If the case remains blocked, inspect the reason instead of editing the database.

### Optional safety cutaway

If there is time outside the submitted video, inspect the existing gas-hazard case and show escalation. Do not spend the main two minutes on a second full storyline. For a live rehearsal, unknown safety facts must remain unknown until explicit evidence arrives.

## 5. Prepare screens, not just narration

- Use the current interface at port 5174 for the main recording. Keep the old interface at 5173 for comparison only; both share the same database.
- Keep the case detail page, the second-account adapter evaluation, and the final evidence slide ready before recording.
- Use the new UI's product preview for at most three seconds. The operational case is the proof, not the animation.
- Close unrelated tabs and notifications; frame the browser so text remains legible at 1080p.
- Show one pointer movement per point. Pause briefly on the report, dependency, action result and score.
- Keep failed or blocked actions visible when discussing recovery. Editing for time must not change the apparent result.
- Reauthenticate to Mubit immediately before capture. If the session expires, use a previously captured, dated screenshot and label it historical.
- Never show environment files, API keys, authentication codes or private mailbox contents.

Existing walkthrough cases and links are in [DEMO_WALKTHROUGH.md](../RepairFlow/docs/DEMO_WALKTHROUGH.md). Verify they still exist before recording; those links refer to the development database, not a public hosted demo.

## 6. Claims checklist for the presenter

| Safe statement, supported by current evidence | Avoid |
|---|---|
| “The second-account adapter scored 11/12 in Mubit internal evaluation.” | “Our model is 91.7% accurate on every real repair.” |
| “Its score exceeds the target, but it needs more judged cases for live readiness.” | “It is deployed and powering this workflow.” |
| “200 requests are recorded; 32 examples were accepted at the observed checkpoint.” | “The adapter trained on all 200 examples.” |
| “We aim to reduce the cost of repeated report decisions.” | “We already save 81%.” |
| “Bookings, reports and tenant replies are simulated.” | “The agent contacted contractors and performed repairs.” |
| “The agent proposes; application checks govern execution.” | “The model can safely handle every possible case.” |

If showing savings, choose one explicitly hypothetical example: 80% successful adapter routing at one-quarter provider inference cost implies 60% lower classifier inference spend before overhead. Do not call that a quote, measured result, or whole-application saving. The simplest two-minute video may omit numerical savings entirely.

## 7. Six-slide PDF deck

1. **Problem — repairs stall between decisions.** One roof-leak timeline with the unresolved handoffs highlighted. Name the users: property managers, tenants and contractors.
2. **Product — an agent that follows through.** One large screenshot with three callouts: evidence, next action, execution result. Mark physical activity as simulated.
3. **Mubit — the learning layer.** Diagram the provider call, example review, specialist adapter and quality gate. Mark application adapter serving as pending.
4. **Evidence — trained, measured, not yet live.** Lead with 91.7% (11/12), target 85%, minimum 20 judged cases. Show 200 recorded requests and distinguish them from 32 accepted examples. Date the observation.
5. **Economics and validation.** Cost-per-correct-decision formula, future measurement plan, independent evaluation status, safety/error metrics. Label all assumed pricing scenarios.
6. **Next milestone and team.** Readiness → verified serving → independent benchmark. Include repository URL, confirmed team names and accurate contribution/provenance statement.

Keep one main claim per slide. Put readable source references in the footer. Use the same vocabulary and numbers as the video; do not mix the original account's 83.3% with the second account's 91.7% as if they were one controlled before/after experiment.

## 8. Rehearsal and failure handling

| Failure | Response |
|---|---|
| Mubit console session expires | Sign in before recording, or show dated saved evidence. Never improvise a current score. |
| Provider responds slowly | Cut the wait in editing and label the transition; retain the actual response/result. |
| Request budget is exhausted | Inspect an existing run or use clearly labeled recorded footage. Do not reset the ledger. |
| Wrong appointment/report selected | Stop, inspect the case and select the correct work scope. Do not force a completion action. |
| Agent escalates or requests information | Show the reason and provide the requested evidence, or use the verified case-history demonstration. |
| Adapter remains in Testing | Keep the current provider workflow and adapter evidence separate; this is the planned baseline. |
| Adapter becomes ready | Verify serving provenance first. Do not assume a green status means the app is using it. |
| New UI interaction fails | Record the working previous UI if necessary and identify it as the demonstrated interface; do not claim the redesign was fully tested. |

Rehearse narration against screen recordings without repeatedly triggering paid decisions. A single new rehearsal, if needed, must fit the existing authorized budget. This plan does not authorize additional collection batches.

## 9. Submission checklist from the supplied event rules

- Confirm team registration, member acceptance and the repository URL captured by Max.
- Confirm both check-ins were actually submitted; drafted answers are not submissions.
- Ask an organizer whether the pre-existing RepairFlow foundation is eligible under the event's code-origin rule. Describe event additions separately; rewritten dates do not establish authorship timing.
- Verify that all live LLM paths used in the submission route through Mubit; avoid a direct-provider configuration during the event demo.
- Export a video under two minutes as MP4 or MOV and a readable PDF deck.
- Open the local exports, check audio and legibility, and verify duration before upload.
- Use the upload page returned by `/submit`. A YouTube link does not satisfy the supplied rules.
- The supplied hard deadline is Sunday 25 October at 05:00; confirm event timezone with organizers if unclear, especially across the UK daylight-saving transition. Submit early rather than relying on the boundary.
- Verify upload success for both files. Updated submissions replace previous submissions until the freeze under the supplied rules.

No submission, organizer message, new training run, or recording was performed merely by creating this plan.
