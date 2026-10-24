# Dev Agent prompt: Fixi UI cleanup

Implement a frontend cleanup of the existing Fixi property repair coordination app. Start from the current redesign in [PR #1](https://github.com/vbshuliar/mubit-hackathon/pull/1), branch `feat/fixi-material-redesign`. This is the property management app, not the older video editor concept in the conversation.

## Understand the current app first

- Repository: `https://github.com/vbshuliar/mubit-hackathon`
- Frontend: `RepairFlow/frontend-fixi`
- Local preview: `http://localhost:5174`
- Read `RepairFlow/CLAUDE.md`, `RepairFlow/docs/APPLICATION_STATE.md`, `RepairFlow/frontend-fixi/docs/DESIGN.md`, `.impeccable/design.json` and `docs/REDESIGN_VERIFICATION.md` before editing. Paths after the frontend path are relative to that folder.
- Inspect the actual pages and existing components in the browser before making changes. Reuse the current component system and dependencies.

The approved direction is professional graphite, titanium, restrained liquid glass and metal, strong typography and purposeful motion. Preserve the opening homepage hero, six-chapter scroll-driven Three.js workflow, Mubit explanation, and the new repair board/portfolio/inbox layout. This task should make the product clearer and more usable within that direction. Avoid another cosmetic colour swap or generic dashboard redesign.

## Priority 1: property history table

Open a property and inspect `src/routes/properties.$propertyId.history.tsx`. The current table has nine columns and a `min-w-[950px]` auto layout. Long Outcome text can dominate the table. Contractor names can also expand it.

- Make widths predictable and balanced. Use explicit column sizing or a fixed table layout where appropriate. The user's request for “the same columns” means consistent proportions; checkbox and action columns should stay narrow, while Issue has enough reading space.
- Keep rows compact and easy to scan. Use consistent alignment, spacing, date formatting and numeric alignment.
- Show a concise Outcome preview with an obvious, accessible way to read the full text, such as an expandable row or detail panel. Choose the simplest approach that fits the existing interface. Do not permanently discard text, depend only on hover tooltips, or let a paragraph determine column width.
- Preserve the difference between status and outcome. Keep useful contractor, quote and navigation information available.
- At mobile widths, use a deliberate compact row/card treatment or contained table scrolling. Prevent page-wide horizontal overflow and inaccessible actions.
- Preserve selection, sorting, navigation, query parameters and CSV export. Export must retain the complete outcome text, regardless of its on-screen presentation.

## Priority 2: unmistakable filters

Trade/tag buttons such as “Roofing” and year buttons such as “2026” currently look like display badges. Make their purpose obvious.

- Consolidate redundant filter rows into one coherent, labelled filter area. For example, use “Trade: All trades” and “Year: All years” controls, a clear selected state, and “Clear filters” when applicable.
- Use real available options; do not hardcode years or trades. Retain the existing trade/year URL state and browser back/forward behaviour.
- Distinguish interactive filters from informational status/tag badges. Do not rely on colour or opacity alone to communicate selection.
- Keep the result count and empty state understandable. Preserve useful chart interactions without repeating the same controls around every chart.

## Priority 3: clean up every page

Review Overview; Maintenance board/list and case detail including Agent/Work; Messages list/thread; Properties directory and each property's History, Details, Documents and Notes; Contractors and contractor detail; Tenants and tenant detail; Insights; Reports; shared navigation, search, dialogs and mobile layouts. Inspect the homepage for consistency, but preserve its approved hero and scroll story.

On each page, clarify the main action, tighten excessive spacing, improve table proportions, shorten redundant headings and helper text, remove repeated decorative labels, and place secondary details behind sensible disclosure. Keep information that helps someone make a repair-management decision. Do not remove working features just to make screenshots cleaner. Prefer a few shared component improvements over unrelated styling on every route.

## Boundaries

Frontend only. Preserve routes, API contracts, query/data hooks, payloads, version guards, validation and permission behaviour. Keep loading, error, empty and pending states usable. Maintain distinctions between simulated records, historical evaluation, model proposals, approvals and actual execution. Do not invent activity, performance claims or missing data. Do not change backend code, database state, provider configuration or model routing. Do not trigger real communications or paid model calls during verification.

## Verification and completion

Implement the changes rather than returning only an audit. Check desktop, tablet, mobile, keyboard navigation and short screens. Use representative long outcomes and contractor names to prove that the table holds its proportions. Verify trade/year selection and clearing, URL restoration, sorting, selection, full-text disclosure, CSV export, case navigation and empty results. Use safe fixtures for mutation paths.

Run the existing unit tests, typecheck, lint relevant to changed files and production build. Update and run the relevant browser checks where the environment supports them. The current verification notes explicitly say that the automated Playwright suite was not rerun for the latest scroll-story iteration; do not present older results as new validation.

Provide before/after screenshots of property history and the other materially changed pages. Update the design/application notes if shared behaviour changes. Finish with the changes made, why information was removed or moved, checks actually run and any remaining issues. Keep the scope focused on cleanup, with no new product features or backend work.
