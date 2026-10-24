# Fixi — autonomous repair coordination

Mubit integration is available: see [configuration and verified scope](docs/MUBIT_INTEGRATION.md).

**Status:** a local repair-agent demo using text intake and explicitly simulated tenant/contractor responses. The agent interprets evidence, proposes a typed action, and the application checks policy before executing it. ElevenLabs, voice sessions and phone dialing have been removed. Historical records are retained.

The demo plan and acceptance criteria are in [DEMO_IMPLEMENTATION_PLAN.md](docs/DEMO_IMPLEMENTATION_PLAN.md). See the [demo walkthrough](docs/DEMO_WALKTHROUGH.md), [verification evidence](docs/DEMO_VERIFICATION.md) and [UI declutter review list](docs/DEMO_DECLUTTER_REVIEW.md). The latest observed Mubit collection results are in [MUBIT_COLLECTION_RESULTS.md](docs/MUBIT_COLLECTION_RESULTS.md); receiving requests is not proof of adapter training or savings.

**New here, or on a new machine?** Read
[docs/APPLICATION_STATE.md](docs/APPLICATION_STATE.md) — the current
account of what works, what does not, and what is undecided — then
*Running locally, from a fresh clone* below.

## The scenario it is built around

Originally the hackathon demonstration, and still the end-to-end case the
whole system is shaped by and tested against.

A roof visit cannot proceed without scaffolding. The coordinator interprets the contractor's report, preserves the original unresolved issue, creates a prerequisite, and blocks roofing. An operator approves the simulated scaffolding commitment. When installation and access handover are reported complete, the original roofing order becomes actionable and is rebooked. Tenant confirmation and all required follow-on work gate resolution.

This full loop passes deterministically end-to-end in `backend/tests/test_hero_path.py` using a scripted fixture coordinator. It has also been exercised manually against the real Gemini API through simpler cases (see docs/26's 2026-09-19 correction entry) — the model correctly proposed a context-specific triage, correctly waited when nothing was actionable, and correctly escalated to a human rather than inventing a contractor when no approved supplier existed for the required trade.

## What's live vs simulated

Contractor organisations, calendars, bookings and physical work are always **SIMULATED** (`MockBookingConnector`; no real contractor is ever contacted, no real booking is ever made).

| Component | Role |
|---|---|
| Mubit + Anthropic coordinator | Real reasoning when explicitly configured; bounded requests, tools, tokens and persistent run count. |
| Text demo responses | Simulated human evidence, never an actual phone call or message. |
| Fixture coordinator | Clearly labelled offline fallback; not a trained model or proof of reasoning quality. |
| Booking connector | Simulated appointment options and commitments; no contractor outreach. |
| Tavily | Optional research evidence; web candidates still require approval. |

## Running locally, from a fresh clone

**[SETUP.md](SETUP.md) is the runbook**: it covers the backend, the
frontend, loading the shared data and starting the app. Each command in
it was run from a fresh clone. In short:

```
cd backend && uv sync --frozen
cd ../frontend-fixi && npm ci && npm run build     # build BEFORE starting the backend
cd ../backend && uv run python -m app.bootstrap    # load the shared workspace
uv run uvicorn app.main:app --port 8000            # http://localhost:8000
```

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/)
(it provisions the pinned Python 3.12 itself) and Node 20+.

**Every clone gets the same data.** `backend/data/` is gitignored, so a
clone starts with no database. `backend/snapshot/workspace.sql` holds
every row of every content table, and `backend/snapshot/files/` holds
every file those rows point at. `app.bootstrap` loads both and then
compares the result with the snapshot row by row. A clone that passes
has the same cases, case numbers, events, messages, costs, notes,
documents and timestamps as the machine that exported it. The property
photographs are frontend assets, committed in `frontend-fixi/src/assets/`.
Two things are deliberately not shared: `.env` (your keys) and one real
tenant phone number (a placeholder stands in). The `jobs` queue is
runtime state and is never captured. SETUP.md has the details, including
how to publish your own changes (`python -m app.workspace --export`) and
how to take someone else's (`python -m app.bootstrap --replace`).

**Build the frontend before starting the backend.** `backend/app/main.py`
mounts the SPA only `if FRONTEND_DIST.is_dir()`, and that check runs
*once, at import time*. Start the backend before `dist/` exists and
`GET /` returns a bare 404 for the life of that process. Run uvicorn from
inside `backend/`, because the project is a uv "virtual" package and is
never installed onto the path. Operator sign-in has been off by default
since 2026-09-21 (`OPERATOR_AUTH_ENABLED` in `config.py`). `GET /healthz`
is the smoke check.

**Where the data came from.** The generators are still how new synthetic
data is authored. After authoring, `app.workspace --export` captures the
result:

```
uv run python -m app.seed                  # 12 properties (with photos), 12 tenants, 24 contractors
uv run python -m app.archive --apply       # 60 closed archival cases, 2021-2026
uv run python -m app.sample_operations --apply # 25 operational cases, dated relative to now
uv run python -m app.archive --validate            # 21 integrity checks
uv run python -m app.legacy_demo_purge --dry-run   # count the scripted demo cases an older build seeded
```

Archival cases are marked with an `archive_batch_id` and are excluded
from every current-workload count, notification and agent wake. They
exist so charts and property history have something to show; they can
never be actioned, and the application works normally without them.

There is one frontend. **`frontend-fixi`** is served -- `main.py`'s
`FRONTEND_DIST` points at `frontend-fixi/dist`. An earlier `frontend/`
app sat alongside it, wired to nothing; it was deleted on 2026-09-21.
Anything in it is recoverable with `git show bd61137:frontend/<path>`.

### Tests

```
cd backend
uv run pytest -q          # 283 backend tests
```

```
cd frontend-fixi
npm test                  # 101 frontend tests (Vitest)
```

Real on-disk SQLite, zero external network calls, and no outreach is
physically possible (see *No-contact guarantee*). The suite deliberately
ignores `backend/.env` -- it used to read it, which made results depend
on one machine's untracked file. Provider-specific tests
(`test_mubit.py`, `test_research.py`)
exercise serialization, parsing and state-transition logic against
synthetic or stubbed data, never a live API -- see docs/22 for the
testing strategy and docs/23 for which live-provider checks have never
been run.

### Text demo and paid-call limits

No phone transport or voice session endpoint is installed. Submitted demo responses
are SIMULATED evidence. The agent still chooses the next action through the ordinary
policy/executor path; response forms cannot directly mark a repair resolved.

`MUBIT_MAX_RUNS` defaults to 30; zero pauses paid decisions. Each attempted run reserves
one entry in `MUBIT_BUDGET_PATH`, which persists across restarts and collection folders.
Failures consume reservations. `MUBIT_MAX_TOKENS_PER_RUN` defaults to 60,000; this is
checked after responses and can overshoot by one response. These limits bound activity,
not provider billing: the application does not know the actual Mubit credit balance.
Review recorded usage and the console before increasing limits. Do not reset the
ledger to repeat a failed collection blindly.

The original database is preserved. Browser demo verification uses
`backend/data/demo-workspace/repairflow.db` with a separate `DATA_DIR`.

## Known limits

- Historical call records remain compatible data; calling and audio controls are removed.
- Email/SMS have no delivery transport. Outward messages remain drafts.
- Model accuracy is evaluated on named scenarios, not guaranteed for arbitrary unseen inputs.
- Mubit adapter availability must be confirmed in its console before claiming improvement.
- This unauthenticated development build must remain on localhost.

## Documentation index

| Read | Document |
|---|---|
| Event and product | [00 Hackathon](docs/00_HACKATHON_CONTEXT.md), [01 Vision](docs/01_PRODUCT_VISION.md) |
| Evidence and competition | [02 Business](docs/02_BUSINESS_PROBLEM_RESEARCH.md), [03 Competitors](docs/03_COMPETITOR_RESEARCH.md) |
| Scope and topology | [04 MVP](docs/04_MVP_SCOPE.md), [05 Architecture](docs/05_SYSTEM_ARCHITECTURE.md) |
| Domain contracts | [06 Models](docs/06_DOMAIN_MODEL.md), [07 State machine](docs/07_CASE_STATE_MACHINE.md) |
| Agent implementation | [08 Agent](docs/08_AGENT_ARCHITECTURE.md), [09 Pydantic AI](docs/09_PYDANTIC_AI_DESIGN.md), [10 Tools](docs/10_TOOL_CATALOG.md) |
| Integrations | [11 ElevenLabs](docs/11_ELEVENLABS_INTEGRATION.md), [12 Tavily](docs/12_TAVILY_INTEGRATION.md), [13 Gemini](docs/13_GEMINI_INTEGRATION.md) |
| Sponsor assessments | [14 Modal](docs/14_MODAL_ASSESSMENT.md), [15 Conduct](docs/15_CONDUCT_ASSESSMENT.md) |
| Interfaces and storage | [16 API](docs/16_API_AND_WEBHOOK_DESIGN.md), [17 Database](docs/17_DATABASE_DESIGN.md) |
| Experience and boundaries | [18 UI](docs/18_FRONTEND_UX.md), [19 Safety](docs/19_SAFETY_AND_ESCALATION.md) |
| Execution | [20 Demo](docs/20_DEMO_SCRIPT.md), [21 Build plan](docs/21_IMPLEMENTATION_PLAN.md), [22 Testing](docs/22_TESTING_STRATEGY.md) |
| Due diligence | [23 Risks](docs/23_RISKS_AND_OPEN_QUESTIONS.md), [24 Sources](docs/24_RESEARCH_SOURCES.md) |
| Review | [25 Questions answered](docs/25_RESEARCH_QUESTIONS_ANSWERED.md), [26 Implementation log](docs/26_SPECIFICATION_REVIEW.md) |
| **Current state of everything** | **[Application state](docs/APPLICATION_STATE.md)** — start here |
| Audit findings | [docs/audit/](docs/audit/) — twelve independent reports |
| Full-application migration | [Handoff](docs/UI2_IMPLEMENTATION_HANDOFF.md), [Interaction inventory](docs/UI2_INTERACTION_CHECKLIST.md), [Working checkpoint](docs/UI2_CHECKPOINT.md), [Queued work](docs/UI2_TODO.md) |

## Properties the system is held to

These were the original MVP acceptance criteria. They are kept because
each is still enforced by a named test, not because the gate still
matters.

One persistent case completes the unexpected dependency loop without direct UI status editing. Duplicate delivery causes no duplicate commitment (`test_phase2_reliability.py`). A backend restart while roofing is blocked preserves the case and allows continuation (`test_phase2_reliability.py`). A gas/electrical-danger variant pauses automation before any model call (`test_coordinator.py`'s hazard-gate test). The UI identifies evidence, proposed action, executed result and simulated activity separately via per-event provenance badges (LIVE/SIMULATED/FIXTURE).
