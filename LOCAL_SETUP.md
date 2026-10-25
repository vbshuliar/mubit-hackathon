# Local setup and project guide

Verified on Windows on 25 October 2026. Repository: `https://github.com/vbshuliar/mubit-hackathon`.

## Open the applications

- FIXI product page: http://localhost:8000
- FIXI populated workspace: http://localhost:8000/maintenance
- Backend API documentation: http://localhost:8000/docs
- Backend health: http://localhost:8000/healthz
- Original Mubit learning lab: http://localhost:3000

Both applications were started in background processes bound to `127.0.0.1` during setup. They are not installed as Windows services and will need starting again after a reboot. Operator login is disabled for this local workspace.

## What this repository is

The main application is **FIXI / RepairFlow**, a property-maintenance coordination workspace. Operators manage properties, tenants, contractors, repair cases, appointments, approvals, costs, documents and messages. The maintenance board shows work in progress, escalations, confirmation waits and completed/cancelled cases. Case pages expose evidence, model proposals, application checks, action execution and a timeline.

The current demo uses text forms to simulate tenant replies and contractor reports. Historical phone records are preserved, but active ElevenLabs/telephone calling has been removed. Booking and physical visits are simulated. Messages are stored locally; an email/SMS delivery transport is not implemented.

The separate root-level learning lab is an earlier support-message classifier. It classifies messages as billing, bug, account or other. It has no database and no third-party Node dependencies. Its offline mode uses simple text rules.

## How the main app works

1. React 19, TanStack Router/Query and Vite render the UI. The built static app is served by FastAPI from `RepairFlow/frontend-fixi/dist`.
2. FastAPI routes in `RepairFlow/backend/app/api` receive case input and persist reported facts with their provenance.
3. SQLite stores the current case/work-order state, append-only events, action records and durable jobs. SQLAlchemy/aiosqlite provide access; SQLite uses WAL and foreign keys.
4. One background worker wakes the coordinator for pending work. Pydantic AI is responsible for live model execution and structured action proposals. Model tools expose scoped reads.
5. Deterministic validation, policy, dependency, approval, version and idempotency checks gate changes in the action executor. A model proposal is not itself an executed action.
6. Work orders, appointments and prerequisites are distinct from the repair case. Completing a visit does not establish that the whole repair is resolved. Required work and tenant-confirmation rules gate closure.
7. The browser polls for progress. The SQLite MVP runs with one backend process; it does not require Docker, PostgreSQL, Redis or a separate queue service.

Mubit can proxy the live coordinator to an Anthropic provider and collect eligible examples for model adaptation. A separate seven-category contractor-report task targets a smaller specialist model. The repository records historical adapter experiments; validated adapter serving, independent accuracy and measured savings are not established. Report shadow measurement is default-off.

## Installed environment

| Component | Installed/verified |
| --- | --- |
| Node.js | 24.13.0 |
| npm | 11.6.2 |
| uv | 0.12.17 |
| Backend Python | 3.12.13, managed by uv |
| Backend environment | `RepairFlow/backend/.venv`, 62 installed packages |
| Frontend dependencies | 461 packages installed using `npm ci` and the committed lockfile |
| Frontend build | `RepairFlow/frontend-fixi/dist` |
| Browser testing | Playwright package plus existing Chrome installation, verified by the browser suite |

The backend lockfile gained `tzdata==2026.5` for Windows. Without it, `ZoneInfo('UTC')` and `ZoneInfo('Europe/London')` fail and valid availability submissions are rejected. The dependency is conditional on `sys_platform == 'win32'`; unrelated locked dependencies were retained.

## Database and files

The populated database is `RepairFlow/backend/data/repairflow.db`. It was restored using the repository's bootstrap command, not regenerated with different dates.

| Data | Count |
| --- | ---: |
| Properties | 12 |
| Tenants | 12 |
| Contractors | 24 |
| Cases | 99 |
| Operational cases | 39 |
| Archival cases | 60 |
| Snapshot content rows | 2,474 across 18 content tables |
| Referenced snapshot files | 15 |

Every snapshot row and file was checked for equality after startup and browser inspection. Runtime jobs are deliberately excluded from the shared snapshot. Ordinary directory views hide archived/sample records by default, so their visible counts can be smaller than database totals.

Snapshot timestamps are preserved. As a result, recent-period reports and upcoming visits may be empty even though historical data is populated. Widen report date filters to inspect that history.

To check the snapshot without replacing your working data:

```powershell
Set-Location 'C:\Users\stast\Desktop\Temp Projects\mubit-hackathon\RepairFlow\backend'
uv run python -m app.bootstrap --check
```

Use `app.bootstrap --replace` only when intentionally resetting the database to the shared snapshot, with the server stopped. It makes a backup first. Do not use the frozen Alembic chain for routine setup: runtime schema initialization and bootstrap are the supported path.

## Start and stop

From the repository root, the helper starts FIXI in the current terminal:

```powershell
.\start-local.ps1
```

Or start each application directly in its own PowerShell terminal:

```powershell
# FIXI
Set-Location 'C:\Users\stast\Desktop\Temp Projects\mubit-hackathon\RepairFlow\backend'
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Original learning lab
Set-Location 'C:\Users\stast\Desktop\Temp Projects\mubit-hackathon'
npm start
```

Use Ctrl+C to stop a foreground server. The current background launches recorded their launcher PIDs in `RepairFlow/backend/data/local-server.pid` and `learning-lab.pid`; those files are a snapshot of this launch, not a permanent process identity. Server logs are in the same directory: `local-server.stdout.log`, `local-server.stderr.log`, `learning-lab.stdout.log` and `learning-lab.stderr.log`.

For frontend development, keep the backend running and use a second terminal:

```powershell
Set-Location 'C:\Users\stast\Desktop\Temp Projects\mubit-hackathon\RepairFlow\frontend-fixi'
npm run dev -- --host 127.0.0.1
# Open http://localhost:5174 (the configured CORS origin).
```

After frontend source changes, `npm run build` updates the static app. Build before starting the backend for the first time; the static mount is checked at backend import time.

## Local configuration and live AI

The ignored `RepairFlow/backend/.env` explicitly selects `COORDINATOR_PROVIDER=fixture`, disables operator auth for localhost, leaves provider keys empty, and turns off Mubit recording/shadow calls. The deterministic fixture can demonstrate guarded local behavior but does not provide full language reasoning or the full live coordinator journey. This setup did not issue paid model calls or train an adapter.

To enable live coordination, put your own Mubit key in that backend `.env`, choose `COORDINATOR_PROVIDER=mubit`, and set the model/base URL according to `RepairFlow/docs/MUBIT_INTEGRATION.md`. The provider account must also be configured in Mubit. Keep the existing budget limits and decide explicitly whether to enable example recording. Restart the backend after changing configuration. Gemini is an explicit alternative; Tavily contractor research is separately optional. Keys stay server-side.

The root learning lab uses its own root `.env` with `MUBIT_API_KEY` and `MUBIT_MODEL`; it does not read the backend's `.env`.

Do not blindly copy the current backend `.env.example` over this working local configuration: that historical example sets operator auth to true, while the current UI has no login form. Use the localhost values above for this local setup.

## Verification and remaining issues

| Check | Result |
| --- | --- |
| Backend frozen dependency sync | Passed |
| Timezone loading, UTC and Europe/London | Passed after adding tzdata |
| Snapshot row/file equality | Passed: 2,474 rows and 15 files |
| Frontend production build | Passed |
| TypeScript | Passed |
| Frontend unit tests | 187 passed |
| Existing Playwright browser tests | 12 passed (mock API fixtures) |
| Backend suite | 464 passed, 2 failed |
| Populated-app browser smoke | 11 routes rendered, no page errors or failed local HTTP responses; mobile dashboard contained |
| Learning lab config/classification | Demo mode; refund example classified as billing |

The two backend failures are the negative/positive cases of `tests/test_limit_replay.py::test_rewind_only_private_copy`. The optional `scripts/replay_limit_failures.py` assumes `chmod(0o600)` creates a private file. Windows does not enforce owner-only access through POSIX mode bits; a Windows ACL implementation and regression coverage are still needed before relying on this utility for private artifacts. It is not used by normal application startup. The assertions were retained, not hidden or skipped.

`npm audit` reported 10 dependency advisories: 5 critical, 3 high and 2 moderate, including TanStack Start/server packages, Vite, Zod, source-map-js and Vitest dependencies. The report is saved locally as `RepairFlow/backend/data/npm-audit.json`. Counts are package advisories, not a proof of exploitability of this static localhost deployment. No forced dependency upgrades were applied because several require changes outside the pinned versions or across major versions. The application should remain local as required by its own project documentation.

Known product limits include simulated availability/bookings, no actual messaging transport, and pending Mubit adapter validation. This setup is not a repository-wide security audit or a claim that every workflow is correct.

Local browser evidence is saved in `RepairFlow/backend/data/browser-smoke.json`, `fixi-dashboard.png` and `fixi-mobile.png`.

## Where to continue reading

- `RepairFlow/CLAUDE.md`: current scope, project rules and documentation precedence.
- `RepairFlow/docs/APPLICATION_STATE.md`: current state and historical corrections.
- `RepairFlow/SETUP.md`: canonical fresh-clone runbook.
- `RepairFlow/docs/DEMO_WALKTHROUGH.md`: intended repair demo journey.
- `RepairFlow/docs/05_SYSTEM_ARCHITECTURE.md`: architecture; newer state/scope entries supersede old voice content.
- `RepairFlow/docs/06_DOMAIN_MODEL.md`, `07_CASE_STATE_MACHINE.md`, `17_DATABASE_DESIGN.md`: contracts.
- `RepairFlow/docs/19_SAFETY_AND_ESCALATION.md`: policy constraints.
- `RepairFlow/docs/MUBIT_INTEGRATION.md`, `ADAPTER_RECOVERY_PLAN.md`: live provider setup and experiment evidence.
- `docs/LEARNING_LAB.md`: separate root-level lab.

No commits, pushes or deployments were performed. The original sibling `Temp Projects/RepairFlow` checkout was not modified.
