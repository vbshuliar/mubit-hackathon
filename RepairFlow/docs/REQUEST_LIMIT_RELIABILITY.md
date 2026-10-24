# Decision limit investigation — 24 October 2026

## Confirmed cause

A controlled repeat of the negative-confirmation scenario failed with `total_tokens_limit`: 5 model responses, 68,089 input tokens and 1,414 output tokens. The configured limit remains 60,000 total tokens; request and tool limits remain 10 and 8. This identifies cumulative tokens, not a request-count limit. Token limits are checked after a response, so one response can cross the allowance. No billing limit was raised.

The historical two failures lacked numeric failure usage, so their individual exact terminal limits cannot be retroactively established. Their repeated 13–15k-token inputs and 4–5 requests match the reproduced failure pattern. A baseline replay also failed with `UnexpectedModelBehavior`; its underlying validation cause was not retained and is unknown.

## First correction and evidence

Unchanged evidence already in the prompt can return a shorter typed reference. Changed or omitted history still returns full evidence, scoped to the case. References are used only when smaller than the original response.

This alone was insufficient: the first pair succeeded, but a repeat follow-up still exceeded total tokens. Preserve that failed result in reporting.

Artifacts under `backend/data/limit-replays/`:
- `62034cff4fd84b56ba48bbf7cce6088f`: old-read baseline, follow-up failed and closure passed.
- `faaac88f2d7e4a6caa461ce17b9b38fb`: shorter reads, both passed.
- `70bb78627d4e4fc297f3f5a9efbf776c`: shorter-read repeat, follow-up exceeded tokens and closure passed.

## Replay limits

States are reconstructed versions 12 and 18 of demo case103 in private SQLite backups. They retain the current roster, policy, availability and clock, and omit historical job/activity flags; these are not byte-identical historical snapshots. No worker executes proposals. Training recording is off, no held-out cases are used, and the shared budget counts every attempt. Original and operational demo databases are not mutated.

Numeric failure usage and an allowlisted limit category are now recorded. Replay diagnostics additionally record captured retry count and the last recognized validation code, never raw exception/provider text. These fields do not claim that the last captured retry was the final failure cause.

Reference: https://pydantic.dev/docs/ai/api/pydantic-ai/usage/ . SDK token limits are cumulative and checked after model responses.

## Second correction

Tool preparation compares the entire scoped database collection with the supplied snapshot and checks the case version before every model request. Only exact, complete and current matches suppress the corresponding report/communication/event read tool. Missing historical records, changed content, stale versions or missing snapshots keep it available. Appointment-slot lookup and research reads remain available. Authority metadata (event actor and communication direction/timestamps) is retained in the prompt. No evidence is silently replaced with guessed summaries.

This changes the tools offered to the model according to available evidence. Compatibility with a future Mubit adapter must be evaluated against this current contract; do not assume an older adapter trained on a different contract is interchangeable.

## Final verification

Artifact `backend/data/limit-replays/59fd106d06a7435981859b605cfb15f4/results.json`: four of four final proposal replays passed (two per reconstructed scenario), with no limit failure or manual retry. Follow-up scheduling: 3 requests, 47,346 and 47,353 total tokens, one appointment lookup and one in-run slot-validation correction each. Closure: 1 request, 17,502 and 17,400 total tokens, no tool calls or validator retry. These are small stochastic samples, not proof every future run succeeds. Proposals were validated, not executed against operational cases.

414 backend tests passed. Independent Python and code reviews approved the changes. Backend restarted with final changes. Both databases pass integrity and foreign-key checks, and operational case103 remains RESOLVED version20. Ten paid decisions were used during diagnosis and comparison; all were recording-off. Shared budget169/180 leaves11 reservations; none of the limits were raised.
