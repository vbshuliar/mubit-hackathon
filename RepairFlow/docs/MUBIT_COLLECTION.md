# Synthetic Mubit collection

The versioned dataset in `backend/app/training_cases.py` has 64 distinct scenarios:
48 training inputs (12 each for plumbing, electrical, roofing and scaffolding)
and 16 held-out inputs (4 each). Expected labels are local scoring data only;
they are never added to the model prompt. This is a narrow next-action dataset,
not a complete repair-lifecycle or safety benchmark.

## Run

From `backend/`:

```
# Prepare 48 cases without a model request:
uv run python -m app.collect_mubit

# Collect provider answers through Mubit (uses provider credits):
uv run python -m app.collect_mubit --live --split train --limit 48

# Evaluate the reserved split; recording is forced OFF:
uv run python -m app.collect_mubit --live --split eval --limit 16
```

Each invocation creates a new directory under `backend/data/mubit-collections/`
with an isolated SQLite database, manifest, results and content-free Mubit metrics.
No operational cases are changed, no worker starts, and no proposed action is
executed. Outreach is disabled. The case builders use application services;
some inherited intake evidence tags say LIVE because those services represent
an intake event, but all content in these collection databases is synthetic.

Runs are sequential, capped at 48 scenarios per invocation, and stop after
three consecutive model errors. Existing coordinator request and timeout limits
also apply. `--offset` and `--limit` allow a deliberate subset. Runs are not
automatically resumed or repeated: a new invocation creates new case/session
IDs, so avoid repeatedly replaying identical inputs to inflate counts.

## Checks and interpretation

Each answer is schema-validated, then checked for action kind, case ID, trigger,
version, trade and preserved safety answers. Scaffolding cases additionally
check report/work-order references and prerequisite kind/trade. A passing score
does not establish policy admission, successful execution, resolution, or absence
of every possible error. Expected actions are developer-authored, not externally
reviewed gold labels. Holdouts are distinct situations in the same narrow families;
they are not an independent real-world benchmark.

Training recording is `full`; evaluation recording is `off`. Recording happens
before local scoring, so even mismatching provider responses may already be in
Mubit. Local failures and expected labels are preserved for review, but this runner
does not upload corrections or claim they changed model weights.

Mubit chooses which examples to keep. Its documented default threshold is 25 kept
examples; raw requests and local passes are not the kept count. Successful-run
tokens/requests are measured. Failed-run token usage may be unknown, so summaries
must not treat these counts as complete billing totals. No dollar savings are inferred.

## Pilot finding and prompt version 2

The completed 48-case collection scored 47/48 with zero request errors. See
[observed results and pending Mubit review](MUBIT_COLLECTION_RESULTS.md).

Initial prompt-version-1 runs exposed skipped triage: the coordinator sometimes
asked for availability or searched for contractors before creating a work order.
The first 4-case pilot matched 3 expected actions. A later batch was stopped after
8 completed cases (and an interrupted ninth) when this pattern persisted.

The dataset builder now shares one four-contractor roster and supplies confirmed
availability. Coordinator prompt version 2 explicitly requires APPLY_TRIAGE for
a case with no work orders and complete nonhazardous safety answers. Unknown
safety answers and hazards retain their separate paths. This is a prompt fix,
not learned adaptation. It creates a new Mubit task fingerprint, so old and new
prompt collection counts must not be added together as one task's examples.

The 16 evaluation scenarios were prepared locally but have not been sent as
training requests. No training threshold or successful adapter is implied by this
document; consult the console and the run summary for observed results.


## Current lifecycle expansion

`--dataset lifecycle` selects 36 additional training cases and 18 held-out cases.
`--dataset safety --split eval` builds six additional held-out safety probes and
refuses training mode. Both preserve the default legacy dataset. The live runner
saves proposals before scoring and stops on evaluator errors or repeated failures.
See [expansion results](MUBIT_TRAINING_EXPANSION.md) before starting more paid runs.
36 cases were collected once; do not replay them to inflate the example count.
