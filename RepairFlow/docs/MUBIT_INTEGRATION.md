# Mubit integration — 24 October 2026

## Repository assessment

This is an existing repair operations product, not a classifier demo. The React/Vite frontend reads FastAPI APIs for properties, tenants, contractors, repair cases, messages, documents, reports and insights. SQLite stores current state and event history. Durable jobs wake a single Pydantic AI coordinator; it receives a snapshot and proposes one typed ActionProposal. Scoped tools read reports, communications, events, appointment options and research. The dispatcher applies hazard and loop-budget checks before reasoning; the executor applies policy, approvals, version checks and idempotency before domain writes. These are the right integration boundaries to preserve.

The model construction site is `app/agents/coordinator.py`. Dynamic case facts are already in the user message, with constant instructions in `instructions.py`, so the recurring task is "choose the next repair coordination action". Switching the provider does not require changing the domain workflow or frontend mutation APIs. Existing orchestration history stores model ID and proposal outcome. The new ID is `mubit/anthropic/<model>`.

Other integrations remain distinct: booking is simulated, Tavily is research, ElevenLabs can use its own hosted conversational model when enabled. ElevenLabs is not routed through Mubit by this change. Leave it in fixture mode for the gateway-only experiment. Legacy direct Gemini remains an explicit configuration option; this local workspace selects Mubit. An all-LLM-calls-through-Mubit submission must not enable a separate hosted voice LLM or direct Gemini path.

## Implemented

- Pydantic AI Anthropic provider with an explicit AsyncAnthropic client pointed at `https://api.mubit.ai/anthropic`; the SDK appends `/v1/messages`.
- Backend-only `MUBIT_API_KEY`; the provider's Anthropic key stays in Mubit. The unrelated Anthropic environment credential cannot accompany this explicit SDK key (covered by the transport test).
- `COORDINATOR_PROVIDER=auto|mubit|gemini|fixture`. Auto selects Mubit when its key is set. Explicit mubit fails startup without its key. Runtime provider errors never silently switch models.
- Configurable `MUBIT_MODEL`, verified locally against the gateway model listing. Local model: `claude-haiku-4-5-20251001`.
- Constant instructions, tools and output schema. Per-case `anthropic_metadata.user_id` groups all wakes and tool round trips for one repair case into a Mubit session, reducing train/test overlap within a case.
- `MUBIT_RECORD=full|metadata|off`. Full is the default; off is for held-out evaluation calls that must not supply training content. Distinct case IDs are still required across dataset splits.
- Existing scoped tools, redaction, bounded requests, structured output, policy and approval checks remain in place. Free-text evidence is not comprehensively anonymized by existing redaction; use synthetic cases for collection experiments.
- `data/mubit-runs.jsonl` contains case/trigger IDs, model/prompt version, gateway request IDs, elapsed time, token usage, request count, proposal action and failure type. It contains no prompt/answer text or keys. `validated_proposal` means schema-valid output, not policy acceptance, successful repair, or benchmark correctness.
- Readiness exposes selected provider/model and whether the Mubit key is configured. This is configuration status, not a continuous connectivity test.

## Setup

Run `uv sync --frozen` in backend. Add to its ignored `.env`:

```
COORDINATOR_PROVIDER=mubit
MUBIT_API_KEY=<your Mubit key>
MUBIT_MODEL=claude-haiku-4-5-20251001
MUBIT_BASE_URL=https://api.mubit.ai/anthropic
MUBIT_RECORD=full
```

Restart the backend. Check `/api/v1/readiness`. Newly triggered agent work uses the gateway; startup does not replay the historical 99 cases into training. Inspect Requests and Tasks in the Mubit console. The frontend remains at http://localhost:5174.

Dependencies: Pydantic AI 2.46.0, Anthropic 1.17.0. Anthropic is constrained below 2 because 2.2/2.3 changed BetaMessageParam to a union that this Pydantic AI version tries to instantiate, raising before any request. Lockfile pins the tested combination. Tests exercise real SDK serialization with a fake HTTP transport.

## Hackathon learning and evaluation plan

The supplied Night Shift guide requires actual model adaptation and evidence of improvement. Gateway integration alone does not satisfy that goal. Public docs describe kept examples, training/testing and console comparisons; they do not establish a correction-label API, programmatic training trigger, or an adapter serving endpoint for this app. No such endpoints are fabricated here.

1. Collect a synthetic training set with varied repair states and known expected actions. Keep instructions, model, tools and schema stable. Whole cases belong to exactly one split.
2. Record baseline quality on a separate fixed test set with recording off. Score action kind, referenced IDs, dependency preservation, policy admission, unsafe actions and task completion in an isolated database. A judge agent can add explanations; deterministic checks should determine factual state changes.
3. Observe kept examples and adapter versions in the Mubit console. The documented default first threshold is 25 kept examples, not 25 calls; a multi-step agent may form more than one task if tool choice or output format changes. Verify actual grouping there.
4. Confirm the event's supported corrections and adapter-serving interfaces with Mubit. Submit corrections and integrate serving only using those confirmed contracts.
5. Evaluate the adapted model on the same held-out cases, compare an unadapted small-model baseline, and report success rate, policy violations, latency and cost per successful task. Current logs provide timing/tokens, not billed dollars or proven savings. Use verified pricing/billing and adapter inference costs for the economic comparison.

This first phase does not claim an adapter has trained, that quality improved, or that costs fell. Broad production readiness and all frontend interactions have not been audited by this integration pass.

## Official sources

- https://docs.mubit.ai/guides/connect-anthropic
- https://docs.mubit.ai/guides/tasks-and-sessions
- https://docs.mubit.ai/reference/api
- https://docs.mubit.ai/guides/first-adapter
- https://ai.pydantic.dev/models/anthropic/

Event context: user-supplied `mubit_night_shift_complete_guide.txt`, prepared 22 October 2026. Treat its proposed implementation ideas separately from verified API capabilities.

## Verification results

- Backend suite: 290 tests passed in 17.75 seconds, including 7 new Mubit transport/configuration cases.
- Live synthetic blocked-roof scenario: expected ADD_PREREQUISITE returned, 2 model requests, 7,464 ms, 17,168 input tokens, 646 output tokens. Proposal only; no operational action executed.
- Shared workspace validation: all 2,474 rows and 15 files still match the snapshot.
- Restarted backend: health, readiness, overview and frontend property page return HTTP 200. Readiness selects Mubit and the verified Claude model.
- Code review: no actionable findings. No adapter training, billing-cost comparison, or live end-to-end repair completion has been verified.
