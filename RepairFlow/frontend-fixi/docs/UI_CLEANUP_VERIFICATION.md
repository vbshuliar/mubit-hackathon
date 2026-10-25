# UI cleanup verification — 25 October 2026

Implemented on `feat/fixi-material-redesign`, following `DEV_AGENT_UI_CLEANUP.md`.
All changes are within `RepairFlow/frontend-fixi/`. The root untracked lockfile was
left alone. Backend, shared records, API contracts and data hooks are unchanged.

## Changes and review

- Property History: predictable column proportions, wrapping issue titles, aligned
  dates/quotes, two-line Outcome previews, keyboard-accessible full-record rows and
  complete CSV export. The scroll region contains the table on narrow screens;
  expanded text stays in the reading viewport. Simulation labels remain visible.
- Repeated chart-adjacent filter chips became one labelled Trade/Year bar. Options
  come from loaded records. Clear filters, sorting, preserved unrelated query
  parameters and browser back/forward are verified through TanStack Router.
- Shared cards now shrink within grids; actions wrap. Fixed mobile overflow in
  property details, tenant details, Insights and Reports, and overlapping tenant
  table columns. Property headers/tabs are more compact and duplicate Edit links
  are removed on the Details tab. Message titles wrap. Recent activity scrolls
  within a bounded reading area instead of stretching both supporting panels.
- Shortened repeated page introductions and empty-state instructions. Kept consent,
  approval, escalation, simulated provenance, quoted/actual costs and model versus
  execution distinctions. No records, counts or dates were changed for presentation.
- Reviewed Overview, Maintenance board/list, case Overview/Agent/Work, Messages
  list/thread, all property tabs, contractor and tenant lists/details, Insights,
  Reports, shared search/dialog/navigation and the homepage. The approved hero,
  six-chapter story and maintenance deck/board remain. One inherited fallback bug
  was fixed: the decorative diagram no longer intercepts chapter-button clicks.

## Actual checks

| Check                           | Result                                                                                                                                                                |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm test`                      | 187 passed across 15 files                                                                                                                                            |
| `npm run typecheck`             | Passed                                                                                                                                                                |
| `npm run lint`                  | 0 errors, 4 inherited warnings (baseline had 5)                                                                                                                       |
| `npm run build`                 | Passed, including SPA prerender `/`                                                                                                                                   |
| `npm run test:browser`          | 12 passed, 30.5 seconds, isolated API fixtures                                                                                                                        |
| Desktop/mobile screen inventory | 16 operational destinations at 1440×1000 and 390×844; no final page overflow or runtime page errors                                                                   |
| Supplemental responsive checks  | Overview, thread, Maintenance, property history, Agent and Work at 1440×1000, 768×1024 and 390×844; no page overflow                                                  |
| Short-screen history            | 844×390; keyboard scroll and case actions reachable                                                                                                                   |
| Long-record fixture             | Compact row under 130px; complete multiline outcome and long contractor name available through disclosure and CSV                                                     |
| History interactions            | Trade/year, empty results, clear, back/forward, retained selection, sort, reload, keyboard disclosure, export and case navigation passed                              |
| Operational behavior            | Synthetic approval/version conflict, rejection reason and response draft retention, search, status/archive filters, New Ticket dialog and mobile navigation passed    |
| Homepage                        | Backend-independent stage/CTA checks, reduced motion and unavailable WebGL fallback passed                                                                            |
| In focus metrics                | API fixture showed 17 active / 6 confirming / 9 resolved this week / 83 total with only one queue item; five-second polling then updated active to 18 and total to 84 |

“In focus” was already connected to `useDashboardMetrics()` and
`GET /api/v1/metrics/dashboard`. Its counts are portfolio totals, independent of
queue filters and limits. The regression test now proves initial rendering and
subsequent polling; no hardcoded values were introduced.

The first current browser run found the inherited diagram click interception. It
was fixed and the complete suite rerun successfully. Intermediate runs also caught
an offscreen table-caption overflow and test-selector issues; final results above
are from the corrected implementation. One overlapping test run lost its temporary
Vite server; the final suite ran sequentially with its own server.

## Screenshots

All screenshots use existing local sample records, with API writes blocked. The
before and after directories use matching names. Open full-size files to compare:

| Screen                  | Before                                                                | After                                                               |
| ----------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| History desktop         | [Before](../artifacts/ui-cleanup/before/property-history-desktop.png) | [After](../artifacts/ui-cleanup/after/property-history-desktop.png) |
| History mobile          | [Before](../artifacts/ui-cleanup/before/property-history-mobile.png)  | [After](../artifacts/ui-cleanup/after/property-history-mobile.png)  |
| Property details mobile | [Before](../artifacts/ui-cleanup/before/property-details-mobile.png)  | [After](../artifacts/ui-cleanup/after/property-details-mobile.png)  |
| Overview desktop        | [Before](../artifacts/ui-cleanup/before/overview-desktop.png)         | [After](../artifacts/ui-cleanup/after/overview-desktop.png)         |
| Thread mobile           | [Before](../artifacts/ui-cleanup/before/messages-detail-mobile.png)   | [After](../artifacts/ui-cleanup/after/messages-detail-mobile.png)   |
| Tenant detail mobile    | [Before](../artifacts/ui-cleanup/before/tenants-detail-mobile.png)    | [After](../artifacts/ui-cleanup/after/tenants-detail-mobile.png)    |
| Insights mobile         | [Before](../artifacts/ui-cleanup/before/insights-mobile.png)          | [After](../artifacts/ui-cleanup/after/insights-mobile.png)          |
| Reports mobile          | [Before](../artifacts/ui-cleanup/before/reports-mobile.png)           | [After](../artifacts/ui-cleanup/after/reports-mobile.png)           |

[Expanded outcome, desktop](../artifacts/ui-cleanup/after/history-expanded-desktop.png)
and [mobile](../artifacts/ui-cleanup/after/history-expanded-mobile.png).
The directories also contain all other reviewed pages, unchanged homepage captures,
Agent/Work and tablet captures. Reproduction scripts:
`scripts/review-cleanup.mjs` and `scripts/capture-cleanup-details.mjs` (local app on
5174; read-only API traffic only). Browser fixtures run independently on 5175.

## Remaining limitations

- Narrow history/directory tables deliberately scroll horizontally; they do not
  collapse into cards. Full history details are readable without wide paragraphs.
- Read-only capture blocks the thread's automatic mark-as-read request. Its error
  toast in mobile screenshots is expected from the capture guard, not a UI regression.
  No communications, shared data writes or paid model calls were forwarded.
- Inherited lint warnings remain in CaseProgress, CaseToolbar, Charts and Insights.
  The property-history memo warning was removed. The lazy 3D bundle still triggers
  Vite's size advisory; Vite also reports the existing tsconfig-path plugin advisory.
  Three.js emits its existing Clock deprecation warning. The deliberate WebGL-failure
  test logs the expected renderer error before the fallback appears.
- No deployment, backend mutation validation or dependency upgrades were performed.
