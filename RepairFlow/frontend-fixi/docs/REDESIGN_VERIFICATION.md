# Frontend redesign verification — 25 October 2026

Scope: only `RepairFlow/frontend-fixi/`. Backend, API types/contracts, data hooks, provider settings, prompts, authorization and orchestration are unchanged. The unrelated untracked repository-root package-lock.json was left alone.

## Delivered

- `/`: backend-independent graphite/titanium product preview, HTML stage controls, lazy Three.js architectural roof/scaffold model, static fallback, responsive real workspace captures and grounded Mubit explanation.
- `/overview`: existing Overview moved intact, with Needs attention first and quieter portfolio metrics.
- Shared satin-silver workspace, grouped graphite navigation, product-preview return link, semantic colors, improved operational type and portal typography.
- Maintenance: compact readable metrics, advanced filters, wrapping issue/property rows, explicit archival sample badges and a purposeful mobile list. Original limits, search, notifications, creation and row actions preserved.
- Cases: recorded blockers, approvals, evidence → proposal → application checks → execution, then contextual simulated response input. Full model/tool details, contractor roster and property history use disclosure. Agent/Work remain React Flow; no operational 3D.
- Mobile case controls wrap, tabs stay within viewport, and the progress rail becomes a readable vertical sequence.

## Checks

| Check | Result |
|---|---|
| `npm test` | 187 passed, 15 files (same baseline count) |
| `npm run test:browser` | 6 passed, fully intercepted synthetic API; no backend required |
| `npm run typecheck` | Passed |
| `npm run lint` | No errors; same 5 pre-existing warnings |
| `npm run build` | Passed, including SPA prerender at `/` |
| Existing route smoke check | Overview, Maintenance, Messages, Properties, Contractors, Tenants, Insights, Reports, ticket Agent and Work loaded |
| Read-only smoke/captures | 0 mutation requests forwarded; no model calls or communications triggered |
| Homepage without API | 0 API requests at desktop, tablet and mobile widths |
| Runtime console | No page errors in the captured normal-WebGL screens or destination smoke check |
| Responsive capture | 1440×1000, 768×1024, 390×844; mobile overflow found and fixed |
| Failure modes | WebGL disabled + reduced motion usable; model success distinct from unrecorded execution; escalation and failed execution prominent |
| Mutation behavior | Synthetic 409 checks preserve response draft/rejection reason; approval uses proposal version 7, rejection uses current version 8 and original payload hash |

Browser tests also cover stage buttons, CTAs, search query forwarding, status/archive filters, creation dialog, mobile drawer, `/overview`, case deep links, Agent and Work navigation. Existing unit tests cover response validation, pending states, appointment identity/draft retention, safety inputs and query behavior.

The screenshots are in [artifacts/redesign](../artifacts/redesign/). Homepage captures show the Coordinated illustrative stage; these are not claims of live activity. Workspace captures use existing sample records read from the local app. Before captures remain local and ignored.

## Performance and motion

React Three Fiber uses demand rendering, capped DPR 1.5, a finite settling camera transition, local generated environment lighting (no HDR fetch), and automatic declarative resource disposal. The scene unmounts offscreen, pauses rendering in hidden documents, and uses instant camera placement for reduced motion. WebGL/context failure is contained by an error boundary; stage text/controls and navigation remain accessible. A Static view control is always available. Route transitions remain owned by the existing router; Motion owns only homepage stage-copy transitions.

The lazy 3D chunk is approximately 993 KB / 269 KB gzip. It is not loaded by operational routes and is deferred on the homepage until the illustration enters view. Vite emits its size advisory; this is not a build failure.

## Known inherited limitations

- Lint warnings: CaseProgress and Charts fast-refresh export conventions; CaseToolbar effect dependency; Insights and property history memo dependencies. No new lint warnings.
- `npm audit`: 10 advisories (2 moderate, 3 high, 5 critical) in existing TanStack Start, Vite/Vitest, source-map-js and Zod dependencies. Every affected installed version matches the starting lockfile. No forced/unrelated framework upgrade performed.
- The product preview intentionally offers direct stages, with no autoplay or scroll hijacking. It is illustrative, not connected to any operational case.
- Component registries were inspiration only; full source/license could not be verified from the supplied component pages, so no registry code was copied.
- Backend/provider behavior was not retested with real mutations or paid model calls. Existing data/state labels and dates were preserved.

## Installed additions

Three.js 0.186.1, React Three Fiber 9.8.2 (React 19 compatible), Drei 10.7.9, Motion 14.6.0 (all MIT); Playwright 1.64.1 (Apache-2.0) for browser checks. Exact resolution is committed in package-lock.json.
