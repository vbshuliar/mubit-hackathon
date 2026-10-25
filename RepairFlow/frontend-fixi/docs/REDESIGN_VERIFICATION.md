# Latest: UI cleanup — 25 October 2026

See [UI cleanup verification](UI_CLEANUP_VERIFICATION.md) for the current 187-unit-test,
12-browser-test results, responsive review and before/after captures. The sections
below document previous milestones.

---

# Scroll story and board redesign verification — 25 October 2026

The latest iteration preserves the approved opening hero, replaces the four-stage
preview with six scroll-linked Three.js chapters, and makes the repair board the
default Maintenance view. This is frontend code plus design/application-state
documentation. Backend code, data, API contracts and provider settings are unchanged.

## Current implementation

- Six chapters cover Report, Coordinate, Review, Resolve, Learn and Evaluate. The
  architectural model transforms into a task-adapter chip. Historical Mubit figures
  are dated and explicitly below readiness gates, not live serving results.
- The scene loads lazily, uses capped DPR and demand rendering, and respects reduced
  motion. It stays mounted after loading but stops active scroll invalidation when
  offscreen or hidden. Diagram view preserves the explanation.
- At heights of 650px or less, chapters use normal document flow and direct controls
  above the content, avoiding clipped sticky navigation.
- Maintenance combines a metal portfolio panel, escalation inbox, visit rail and
  four workflow lanes. The original list, filters, search and row actions remain.
- Desktop sidebar overflow is scrollable. All up to five passed visits render,
  matching the shown count. No property-table or cross-page cleanup is included yet.

## Validation

- All 187 existing offline unit tests passed (15 files).
- TypeScript, production build and ESLint on changed frontend source passed.
- Browser checks at 1280×720 and 390×844 verified actual scroll-driven 3D,
  chapter jumps, board/list switching and status filtering. Console checks found
  no errors. Read-only interactions did not submit operational actions or call models.
- Additional 390×600 and 844×390 checks verified the short-height fallback;
  1280×720 sidebar scrolling reached the operator account.
- Independent review scored its three findings resolved: sidebar overflow,
  short-screen clipping and displayed visit count. The nonempty visit branch was
  verified in source because the live dataset had no upcoming visits.
- Browser test/capture selectors have been updated for the new chapters and default
  board. **The full automated Playwright suite was not rerun for this iteration.**
  The six-test result below belongs to the earlier UI, not the current one.
- The optional Impeccable detector was unavailable because its engine was not
  installed. Source, browser and independent visual review were used.

Latest captures: [scroll-story board screenshots](../artifacts/redesign/scroll-story/).
The earlier images remain as historical evidence. The existing lazy Three.js bundle
still produces Vite's large-chunk advisory; no framework or dependency upgrades
were made in this iteration.

---

## Historical verification: initial material redesign

The following record describes the earlier four-stage implementation and its test
run. Its screenshots, motion details and checks must not be read as current.

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

| Check                      | Result                                                                                                                                                      |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm test`                 | 187 passed, 15 files (same baseline count)                                                                                                                  |
| `npm run test:browser`     | 6 passed, fully intercepted synthetic API; no backend required                                                                                              |
| `npm run typecheck`        | Passed                                                                                                                                                      |
| `npm run lint`             | No errors; same 5 pre-existing warnings                                                                                                                     |
| `npm run build`            | Passed, including SPA prerender at `/`                                                                                                                      |
| Existing route smoke check | Overview, Maintenance, Messages, Properties, Contractors, Tenants, Insights, Reports, ticket Agent and Work loaded                                          |
| Read-only smoke/captures   | 0 mutation requests forwarded; no model calls or communications triggered                                                                                   |
| Homepage without API       | 0 API requests at desktop, tablet and mobile widths                                                                                                         |
| Runtime console            | No page errors in the captured normal-WebGL screens or destination smoke check                                                                              |
| Responsive capture         | 1440×1000, 768×1024, 390×844; mobile overflow found and fixed                                                                                               |
| Failure modes              | WebGL disabled + reduced motion usable; model success distinct from unrecorded execution; escalation and failed execution prominent                         |
| Mutation behavior          | Synthetic 409 checks preserve response draft/rejection reason; approval uses proposal version 7, rejection uses current version 8 and original payload hash |

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
