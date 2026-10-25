# Session handoff supplement

Prepared 25 October 2026 from this development session and local verification. This file captures operational context missing from the existing project documentation. It is not a new product specification or a live Mubit status feed. Credentials and authentication codes are intentionally omitted.

## Two UI versions are available on the development machine

The user requested a side-by-side comparison after the frontend redesign was merged.

| Version | URL | Source directory |
|---|---|---|
| Previous interface | http://localhost:5173/ | `/Users/admin/projects/mubit-ui-preview-old` |
| Current interface | http://localhost:5174/ | `/Users/admin/projects/mubit-hackathon/RepairFlow/frontend-fixi` |
| Shared API | http://localhost:8000/ | `/Users/admin/projects/mubit-hackathon/RepairFlow/backend` |

Both UI endpoints returned HTTP 200 and the backend health check returned `{"status":"ok"}` during preparation of this note. This verifies availability, not a new end-to-end acceptance run.

The previous interface is an exported source snapshot from before the redesign, not a Git checkout or submodule. It was exported from the then-current commit `ede0a2f`; that historical ID is retained in the external backup history and should not be assumed to exist in a fresh clone of current main. Its dependencies were installed separately. It is local-only and is not included when cloning this repository.

Both interfaces connect to the same backend and demo database. Editing a case in either interface changes what the other displays. They are not independent test environments. The backend was started with the existing demo-workspace database and `FIXI_NO_CONTACT=1`.

To restart only the previous interface on this machine:

```sh
cd /Users/admin/projects/mubit-ui-preview-old
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

The current UI was started with `npm run dev -- --host 127.0.0.1 --port 5174`. Use `localhost` in browser URLs: the backend's documented default CORS allow-list includes localhost on these ports. Process IDs and terminal session handles are deliberately omitted because they are transient.

## Latest frontend pull and validation scope

The redesign arrived through PR #1, `feat/fixi-material-redesign`, attributed by the user to Yakivets. It was pulled before either UI was started for comparison. After the pull, `npm ci --no-audit --no-fund` and `npm run build` completed successfully. The working tree was clean at that point.

No new browser regression suite was run in that pull/start turn. A successful production build is not evidence that every redesigned interaction was manually tested. The frontend's existing README describes the new routes and browser tests; it need not be duplicated here.

## Local recovery material outside the repository

The following recovery files were verified to exist on the development machine:

| Location | Purpose |
|---|---|
| `/Users/admin/repository-backups/mubit-hackathon-20261024/RepairFlow.git` | Original nested RepairFlow Git metadata, moved out when consolidating into one repository. |
| `/Users/admin/repository-backups/mubit-hackathon-20261024/before-author-date-rewrite.bundle` | Git history backup before the first author-date rewrite. |
| `/Users/admin/repository-backups/mubit-hackathon-20261024/before-expanded-history.bundle` | Git history backup before large commits were split into smaller commits. |

These are local recovery resources, not remote backups or files shipped with the application. Preserve them if old commit references or collaborators' old history need to be inspected.

The published main branch has been rewritten since the frontend PR was merged. A collaborator holding the previous history should preserve local work before resynchronizing and should not merge the old main history back into the rewritten branch. The source tree was checked for equality during the rewrite. The current branch tip at this note's preparation was `1f219245f57f47562270f7dc5022611c08298d7d`; this is a reference point, not a permanent latest-version identifier.

## Mubit authentication and monitoring handoff

The second workspace is identified reliably by the console name **Terdessa** and project ID recorded in the adapter recovery log. A second-account email previously remembered in the chat was rejected with “Identifier is invalid.” The user subsequently signed in manually. The correct second-account login email was not independently confirmed; do not reuse the rejected address as an established account identifier.

Mubit sessions expired repeatedly during monitoring. The last successful second-account inspection is in the recovery log. A later scheduled check at **01:06 UTC on 25 October 2026** found the console signed out again, so no later readiness status was verified in that check.

The connected Gmail tool withheld authentication codes during an earlier login attempt. User-provided codes or an interactive user login were used instead. Do not assume that permission to read Gmail makes an authentication code retrievable through that connector.

An hourly follow-up named `finish-mubit-adapter-validation` has been configured in the Codex desktop app. Its local configuration belongs to the app, not this repository, and does not travel with a clone. It monitors readiness and preserves the independent evaluation set. It must not replay the previously approved extra 100 calls or initiate new paid collection automatically. Its notification preference is meaningful changes only; repeated unchanged pending states should stay quiet. Inspect the automation before changing it because its current state may differ from this session record.

## What the timing estimate does—and does not—show

The chat estimated approximately **seven hours** from finishing the second-account batch to the appearance of its first above-target result. This was inferred from the recorded batch completion time and rounded console labels such as “4 h ago” and “1 h ago,” not exact training-job start/end timestamps.

That estimate combines ingestion, review, queueing, training, and evaluation. It must not be described as seven hours of GPU training or a guaranteed Mubit turnaround time. Exact per-stage timing remains unknown.

Use UTC timestamps or explicit Europe/London timezone conversion when comparing later checks: the UK daylight-saving transition occurs on 25 October 2026, so local hour labels can be ambiguous.

## Unresolved question: how to expand the judged test set

The key unresolved question is whether the remaining review backlog will expand the current adapter version's evaluation, create a new version with a different evaluation set, or require another platform action. No supported manual evaluation-expansion or rerun operation was established during this session.

An additional request is not automatically an additional judged case. Reviewing every remaining example is not a verified guarantee of readiness. Conversely, readiness might be reached before the backlog is exhausted if enough suitable cases are judged and all gates pass.

For the previously observed 11 correct out of 12, reaching exactly 20 judged cases at an 85% threshold would require at least 17 correct overall: **at least six of eight additional cases must pass**. This arithmetic assumes the same version and cumulative test set; it is not a prediction of how Mubit constructs its evaluations.

A useful support question was drafted for the user, but this assistant did not submit it: “How can we advance this version from 12 to at least 20 judged cases? Does review of the existing backlog automatically expand its evaluation, or is a separate training/evaluation step required?” No support response is known from this session.

## Documentation freshness and remaining publication work

The root README still presents the original account's adapter result. The newer second-account result is already recorded in `RepairFlow/docs/ADAPTER_RECOVERY_PLAN.md`, so it is intentionally not copied into this supplement. Updating the README to distinguish both accounts remains outstanding.

At this supplement's creation, that second-account recovery-log addition was an existing **uncommitted local change**. A fresh remote clone therefore should not be assumed to contain it. Creating this supplement does not by itself publish either file.

The check-in answers drafted in chat are drafts only. The assistant did not submit the Night Shift form, send an external support message, or verify the complete team email list.

The user reported that judges did not require ElevenLabs or actual phone calling. That feedback was the reason for prioritizing visible text-driven simulation and agent decision evidence over telephony; the resulting implementation is already described in the project docs.

## Existing sources to consult rather than duplicate

- [Adapter recovery log](../RepairFlow/docs/ADAPTER_RECOVERY_PLAN.md): account-specific observations, scores, IDs, gates, and experiment history.
- [Fresh collection record](../RepairFlow/docs/MUBIT_FRESH_COLLECTION.md): approved request counts, key configuration incident, and budget history.
- [Documentation audit](../RepairFlow/docs/MUBIT_DOCUMENTATION_AUDIT.md): documented API limits and serving/evaluation uncertainties.
- [Frontend README](../RepairFlow/frontend-fixi/README.md): current UI entry points and test commands.
- [Demo verification](../RepairFlow/docs/DEMO_VERIFICATION.md): previously exercised browser scenarios and their limitations.

When sources conflict, compare their observation dates and scope. An older “no adapter” result can remain valid historical evidence without describing the current account state.
