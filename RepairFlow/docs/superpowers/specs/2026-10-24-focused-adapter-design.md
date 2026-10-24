# Focused Mubit adapter for RepairFlow

## Product decision
Use the frozen contractor-report classifier as a bounded component of the central repair coordinator. A report is recurring unstructured input with a small, meaningful set of outcomes. Whole-case planning includes IDs, variable tool sequences and many state transitions; current coordinator adapters scored7.7%/13.3%. More of that traffic alone is not a sound optimization strategy.

## Frozen learning contract
Existing report-classification-v2 instructions, report_decision tool schema, model claude-haiku-4-5-20251001. Input only assigned work scope and report text. Output COMPLETED, NO_ACCESS, NO_SHOW, FAILED, SCAFFOLD_REQUIRED, CLARIFY or ESCALATE. No IDs, expected labels, action history or unstable tool menus in the learned task. Keep the existing56training/14development/28evaluation split. Do not tune using evaluation failures; retire exposed evaluation sets and author fresh holdouts for subsequent rounds.

## Application connection
Default-off shadow mode inside the existing Mubit coordinator. Extract one authoritative pending report only when all scope/source/version relationships can be established. Keep domain executor and policy authoritative. Shadow records a classification for comparison, never changes operational decisions. Recording off in shadow; fixed prompt and schema unchanged. Unknown routing provenance remains explicitly unknown, and requests made to a teacher are not reported as adapter inference.

After a passing, servable adapter and independent evaluation, implement a separate opt-in guarded action path mapping eligible classifications to existing typed proposals. Missing, ambiguous, unsafe or unsupported cases retain the current coordinator/human escalation. Do not close a repair based solely on contractor completion: tenant confirmation and outstanding work checks remain mandatory.

## Gates
1. Offline extraction, no-contact, budget, cancellation and operational behavior tests pass.
2. Mubit finishes reviewing recorded examples and trains a version. Only add targeted examples when evidence identifies a shortage or weakness.
3. Adapter passes actual Mubit gate (which may exceed80%); never lower threshold for appearance.
4. Independent unseen accuracy at least80%, report per-class counts and sample uncertainty, zero unsafe false-completion on safety probes. Require actual served adapter/version/fallback evidence.
5. Compare teacher, base+prompt, adapter quality, latency and measured cost. No inference of savings from token counts alone.
6. Enable operational mapping only after validation; shadow integration alone is not completed adaptation.

## Current dependency
Task ln_2595e659e1342478d5f8616d has56calls and0accepted as of24October2026 14:46UTC; review pending. The external service controls training and readiness. No promise of80% until measured.
