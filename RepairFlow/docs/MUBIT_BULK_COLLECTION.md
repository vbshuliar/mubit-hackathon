# Additional Mubit collection — 24 October 2026

## Completed

The user explicitly authorized 300 additional application-shaped requests. Sent 300 contractor-report classifications in five sequential batches of 60, through the existing frozen report-classification-v2 contract and Claude Haiku 4.5 gateway. All requests recorded in full. No operational actions or repair database changes were executed.

Data comprises 60 authored scenario families with five language variants each, not 300 independent situations. Every batch covers all seven classes. The 28 final evaluation cases were not submitted. General and Python reviewers approved the dataset and runner changes; 24 related offline tests passed.

## Results

| Class | Expected decisions matched |
|---|---:|
| Completed | 45/45 |
| No access | 43/45 |
| No show | 45/45 |
| Failed | 45/45 |
| Scaffold required | 40/40 |
| Clarification needed | 35/40 |
| Escalate | 40/40 |
| **Total** | **293/300 (97.7%)** |

No request errors, retries, or unsafe false completions. Exactly 300 provider requests, 331,586 input tokens and 12,032 output tokens. This is synthetic collection agreement with locally authored expected labels, not independent benchmark accuracy, and not evidence of a trained adapter's accuracy. Console sampled requests explicitly say “Your provider.”

Seven mismatches: family48 variants1,2,3,5 (unrelated repair evidence), family16 variants2,4 (attended but no entry confused with no-show), family51 variant5 (instruction-only report). All are retained in the mismatch artifact. Family48 variant1 was rated Bad with a correction in Mubit; saved console request01a16e8b-ad35-7083-8a4a-fe4c91030551. The six other mismatches are only flagged locally. Rating does not prove that Mubit uses a replacement training target.

## Evidence

- backend/data/report-task-runs/bulk-20261024-b1 through b5: individual manifests, responses, request IDs and summaries.
- backend/data/report-task-runs/bulk-20261024-summary.json: combined metrics.
- backend/data/report-task-runs/bulk-20261024-mismatches.json: seven mismatches.
- docs/demo-evidence/bulk-feedback.png: saved Bad rating.

## Budget and application

Shared ledger increased253→553; it was not reset. The operational ceiling increased264→564 solely to preserve the original11 remaining demo reservations. Backend restarted on the same no-contact demo database; health check returned OK. No trained adapter enabled and no decision logic changed. Token totals are measured; actual dollar charges and remaining provider balance are not verified.

## Mubit status

At16:38BST the task traffic chart showed310 calls (up from56) while its header still showed56. New calls are being assigned to the same classifier task, but UI aggregation is delayed. Kept examples remained0 and status remained Reviewing examples. Do not claim all300 are reviewed, accepted or trained. No further automatic paid collection is authorized by this completed batch. Next useful step is review/training progress, then provenance-verified independent evaluation of a passing adapter.
