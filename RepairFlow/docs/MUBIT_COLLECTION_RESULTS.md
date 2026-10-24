# Mubit collection results — 24 October 2026

## Completed batch

Dataset v2 contains 64 distinct synthetic scenarios: 48 for collection and 16
held out for later evaluation. Families cover plumbing, electrical and roofing
triage, plus scaffolding prerequisites after a contractor report.

Run: `backend/data/mubit-collections/20261024T021524-930b3c9a/`

| Measure | Result |
| --- | --- |
| Coordinator prompt | Version 2 |
| Provider model | claude-haiku-4-5-20251001 |
| Scenarios completed | 48 / 48 |
| Local checks passed | 47 / 48 (97.9%) |
| Request errors | 0 |
| Model requests | 111 |
| Input / output tokens | 839,116 / 34,651 |
| Sum of coordinator durations | 357,033 ms |
| Recording | full |

These are narrow next-action checks on collection data, not an unseen benchmark,
proof of learned improvement, or a cost comparison. The model produced proposals
only; none were executed. The failed case, `v2-roofing-08`, asked for confirmation
instead of applying triage despite complete nonhazardous safety answers. Its full
proposal and scoring failure remain in `results.jsonl`.

The earlier pilot and interrupted prompt-version-1 batch remain in separate
folders. The subsequent prompt correction must not be attributed to Mubit learning.
The 16 holdout cases were built locally but were not sent to Mubit.

## Mubit console observation

At approximately 02:22 UTC on 24 October 2026, the new task
[Coordinate unresolved property 2](https://app.mubit.ai/console/projects/ws-f7685debbc87c0ad/workloads/ln_1671a75b313fb646a60aa1be)
showed:

- Status: Reviewing examples.
- Examples: 0 kept, 0 rejected, 105 waiting for review.
- Review today: 13 queued, 0 over today's limit, 1 running.
- First training: not started. Routes: none.
- No adapter or learnings had been confirmed.

These are asynchronous console observations, not expected to equal the local
request total immediately. The separate traffic metrics panel reports an access
error (`reading ... metrics needs manager`), so its figures are unavailable.
Task review details are still visible. We did not change permissions or training
policy. The older prompt has a separate task named Coordinate unresolved property.

The [official guide](https://docs.mubit.ai/guides/first-adapter) says the default
first-training threshold is 25 kept examples, and not every call is kept. The
current queue is awaiting Mubit processing; more duplicate requests are not yet
justified. Recheck this task after review. If it reports too few examples, add new
collection scenarios with the same instructions and tool schema. If training
passes, compare the adapter with the provider on the reserved holdout cases,
without recording those cases as training data.

## Verification

- Backend suite: 292 tests passed.
- Read-only code review completed; no outstanding findings.
- Shared database: all 2,474 rows match its snapshot; all 15 files byte-identical.
- Backend restarted with prompt version 2; health and readiness succeed with Mubit.
- No tenants or contractors contacted; collection uses a separate SQLite database.

See [collection runbook](MUBIT_COLLECTION.md) for repeatable commands and limits.
