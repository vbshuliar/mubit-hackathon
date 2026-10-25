# Setup: from a fresh clone to the running app

Every command here was run, in this order, from a fresh `git clone` on
2026-10-24 and produced the output shown. At the end you have the same
database as everyone else: same properties, tenants, contractors, 99
cases, events, messages, costs, notes, documents and timestamps, checked
row by row.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/). It
  installs the pinned Python (3.12) itself, so no system Python is needed.
- Node 20 or newer, with npm.

Commands are shown for a POSIX shell. They are identical in PowerShell
except where noted.

## 1. Backend dependencies

```
cd backend
uv sync --frozen
```

This creates `backend/.venv` from `uv.lock`. It takes about 10 seconds.

On Windows the lockfile also installs `tzdata`. Windows does not normally
provide the IANA database required by Python's `zoneinfo`; without this
package, valid `UTC` and `Europe/London` availability submissions fail with
`Unknown availability timezone`.

## 2. Frontend build (before you start the backend)

```
cd ../frontend-fixi
npm ci
npm run build
```

This writes `frontend-fixi/dist/`. **Build first.** The backend checks
for `dist/` once, when it starts. If you start it before building,
`http://localhost:8000` returns 404 until you restart the backend.

## 3. Load the shared data

```
cd ../backend
uv run python -m app.bootstrap
```

This creates `backend/data/repairflow.db` and loads
`backend/snapshot/workspace.sql` into it. It then copies the files in
`backend/snapshot/files/` into `backend/data/` and validates the result:

```
Loaded the shared workspace: 2474 row(s), 15 file(s).

Validating against backend/snapshot/:
  [PASS] snapshot_present: 2474 row(s) across 18 table(s)
  [PASS] database_matches_snapshot: all 2474 row(s) identical
  [PASS] every_snapshot_file_is_on_disk: 15/15 file(s) present and byte-identical

Database:
  properties                12
  tenants                   12
  contractors               24
  cases (total)             99
  cases (operational)       39
  cases (archival)          60
```

`database_matches_snapshot` is the check that matters. It compares every
row, not counts. Run `uv run python -m app.bootstrap --check` at any time
to compare your database with the snapshot without writing anything.

The property photographs are frontend assets in
`frontend-fixi/src/assets/`, so step 2 already included them.

## 4. Start the app

```
uv run uvicorn app.main:app --port 8000
```

Run it from inside `backend/`. Then open **http://localhost:8000**. There
is no sign-in screen; operator auth is off by default.
`http://localhost:8000/healthz` returns `{"status":"ok"}`.

That's it. Stop the server with Ctrl+C.

## Optional

### Provider keys

Everything works without a `.env`. The coordinator then uses a labelled
offline fixture instead of Gemini, and voice and research stay in
fixture mode. To use the real providers:

```
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
```

Then fill in the keys. `.env` is gitignored, so keys never reach the repo.

### Frontend with hot reload

Keep the backend running on port 8000, then in a second terminal:

```
cd frontend-fixi
npm run dev                 # http://localhost:5174
```

### Tests

```
cd backend && uv run pytest -q       # 283 tests, about 45 s, fully offline
cd frontend-fixi && npm test         # 101 tests
```

The backend suite never touches `backend/data/` and cannot place a call
or send a message.

## Keeping everyone's data the same

`backend/snapshot/` is the shared data. Your own `backend/data/` is a
local working copy, and git ignores it.

**You changed data in the app and everyone should have it:**

```
cd backend
uv run python -m app.workspace --export
git add snapshot && git commit -m "Update the shared workspace"
```

The export reads your database read-only, so the server can keep
running. It refuses to write a phone number that isn't a placeholder, an
email address or anything shaped like an API key.

**Someone else updated the snapshot and you want their data:** pull,
**stop the server**, then:

```
uv run python -m app.bootstrap --replace
```

This first copies your current database to
`data/repairflow.db.before-replace-<timestamp>`, then loads the
snapshot. Bootstrap never merges the snapshot into a database that
already has data. Without `--replace` it only reports how yours differs.

### What is deliberately not shared

- **`backend/.env`**: your API keys.
- **One real phone number.** The source machine keeps a real mobile on
  one tenant so live calls reach a test phone. The snapshot carries that
  tenant's placeholder, `+441179460000`, instead.
- **The `jobs` table**, the agent's wake-up queue. It is runtime state.
  Replaying it would make the agent act on cases on someone else's
  machine.
- **Call recordings that no call points at.** The snapshot carries every
  file a database row references. Anything else in `data/recordings/` is
  not part of the workspace.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `http://localhost:8000` returns 404 | The backend started before `npm run build`. Build, then restart uvicorn. |
| `ModuleNotFoundError: No module named 'app'` | uvicorn was started outside `backend/`. `cd backend` first. |
| `--check` says rows are absent or different | Your database has diverged from the snapshot. Use `--replace` to take the snapshot, or `app.workspace --export` to publish yours. |
