---
name: "Fixi"
description: "Graphite, titanium and glass for visible repair coordination."
colors:
  primary: "oklch(0.49 0.1 162)"
  primary-foreground: "oklch(0.99 0.005 160)"
  primary-soft: "oklch(0.95 0.03 160)"
  background: "oklch(0.965 0.004 240)"
  foreground: "oklch(0.25 0.014 250)"
  card: "oklch(1 0 0)"
  card-foreground: "oklch(0.21 0.034 264.7)"
  popover: "oklch(1 0 0)"
  popover-foreground: "oklch(0.21 0.034 264.7)"
  secondary: "oklch(0.955 0.006 250)"
  secondary-foreground: "oklch(0.3 0.03 264)"
  muted: "oklch(0.965 0.005 250)"
  muted-foreground: "oklch(0.48 0.018 250)"
  accent: "oklch(0.955 0.006 250)"
  accent-foreground: "oklch(0.21 0.034 264.7)"
  destructive: "oklch(0.577 0.245 27.325)"
  destructive-foreground: "oklch(0.984 0.003 247.858)"
  border: "oklch(0.87 0.009 250)"
  input: "oklch(0.8 0.012 250)"
  ring: "oklch(0.49 0.1 162)"
  sidebar: "oklch(0.235 0.012 250)"
  sidebar-foreground: "oklch(0.85 0.008 250)"
  sidebar-accent: "oklch(0.32 0.015 250)"
  sidebar-border: "oklch(0.37 0.012 250)"
  surface-satin: "oklch(0.95 0.005 240)"
  surface-glass: "oklch(1 0 0 / 0.84)"
  preview-bg: "oklch(0.185 0.008 250)"
  preview-text: "oklch(0.95 0.005 220)"
  preview-muted: "oklch(0.74 0.012 220)"
  preview-line: "oklch(0.43 0.012 220 / 0.55)"
  preview-emerald: "oklch(0.8 0.1 165)"
  status-red: "oklch(0.95 0.03 20)"
  status-red-foreground: "oklch(0.5 0.18 25)"
  status-orange: "oklch(0.96 0.04 70)"
  status-orange-foreground: "oklch(0.48 0.13 55)"
  status-green: "oklch(0.95 0.04 155)"
  status-green-foreground: "oklch(0.45 0.11 155)"
  status-blue: "oklch(0.95 0.03 250)"
  status-blue-foreground: "oklch(0.5 0.17 258)"
  status-amber: "oklch(0.96 0.05 85)"
  status-amber-foreground: "oklch(0.48 0.11 70)"
  status-purple: "oklch(0.955 0.03 300)"
  status-purple-foreground: "oklch(0.5 0.17 300)"
  status-gray: "oklch(0.955 0.005 250)"
  status-gray-foreground: "oklch(0.45 0.02 260)"
  sidebar-graphite: "oklch(0.2 0.012 230)"
  workflow-bg: "oklch(0.17 0.008 240)"
  board-paper: "oklch(0.998 0.001 220)"
  board-lane: "oklch(0.92 0.008 220 / 0.65)"
  search-surface: "oklch(0.94 0.008 220)"
typography:
  display:
    fontFamily: '"Inter", sans-serif'
    fontSize: "clamp(56px, 6.8vw, 96px)"
    fontWeight: 500
    lineHeight: 1.02
    letterSpacing: "-0.04em"
  headline-workflow:
    fontFamily: '"Inter", sans-serif'
    fontSize: "clamp(36px, 4.35vw, 66px)"
    fontWeight: 500
    lineHeight: 1.08
    letterSpacing: "-0.04em"
  title-operations:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "32px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.04em"
  title-board:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "0.875rem"
    lineHeight: "1.4rem"
  body-workflow:
    fontFamily: '"Inter", sans-serif'
    fontSize: "16px"
    lineHeight: 1.8
  label-board:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "10px"
    lineHeight: 1.5
  label-nav:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "10px"
    fontWeight: 500
    letterSpacing: "0.1em"
  metric-portfolio:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "29px"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  button:
    fontFamily: '"Inter", ui-sans-serif, system-ui, sans-serif'
    fontSize: "14px"
    fontWeight: 600
    lineHeight: "1.4rem"
  button-preview:
    fontFamily: '"Inter", sans-serif'
    fontSize: "14px"
    fontWeight: 600
rounded:
  sm: "8px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  workflow-evidence: "14px"
spacing:
  compact: "8px"
  card: "12px"
  comfortable: "16px"
  deck-gap: "18px"
  content: "20px"
  section: "24px"
  portfolio: "26px"
  wide-gutter: "28px"
  preview-gutter: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-destructive:
    backgroundColor: "{colors.destructive}"
    textColor: "{colors.destructive-foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.secondary-foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.button}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    height: "36px"
  button-silver:
    textColor: "oklch(0.23 0.01 240)"
    typography: "{typography.button-preview}"
    rounded: "{rounded.sm}"
    padding: "14px 21px"
  input-search:
    backgroundColor: "{colors.search-surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.sm}"
    padding: "0 12px"
    height: "40px"
    width: "min(440px, 50vw)"
  nav-item:
    textColor: "{colors.sidebar-foreground}"
    rounded: "{rounded.lg}"
    padding: "0 12px"
    height: "41px"
  chip-urgent:
    backgroundColor: "{colors.status-orange}"
    textColor: "{colors.status-orange-foreground}"
    rounded: "{rounded.md}"
    padding: "3px 6px"
  card-board:
    backgroundColor: "{colors.board-paper}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    padding: "12px"
  workflow-evidence:
    textColor: "{colors.preview-text}"
    rounded: "{rounded.workflow-evidence}"
    padding: "20px 24px"
---

# Design System: Fixi

## Overview

**Creative North Star: "Graphite, titanium and glass"**

The approved graphite-and-mint hero remains the visual anchor. The system pairs this dark architectural presentation with a satin titanium workspace, graphite grouped navigation and restrained emerald emphasis. Metal reflections define the major surfaces; glass gives evidence and floating chrome a distinct layer.

Working information stays legible on pale cards with a compact hierarchy. The portfolio panel, attention inbox and visit rail establish the scan order above the repair board. Materials support the relationship between evidence, decisions and outcomes without changing the meaning of operational states.

**Key Characteristics:**

- Preserved graphite-and-mint hero with silver calls to action.
- Satin workspace, graphite navigation and opaque case cards.
- Compact operational hierarchy with explicit state labels.
- Scroll-linked architectural story with manual chapters and a diagram alternative.

This is the approved frontend design record. It refreshes the existing `docs/DESIGN.md` in its established location; no `PRODUCT.md` exists, and this document does not invent one. Token values were extracted from `src/styles.css`, `src/components/preview/preview.css`, `src/components/preview/workflow.css` and `src/components/fixi/operations.css`. Components were checked against their finished source and the staged desktop/mobile review images. The frontmatter owns primitives; `.impeccable/design.json` carries shadows, motion, breakpoints and standalone component examples. Sidecar tonal ramps are display aids synthesized from the source colors, not additional application tokens.

The scope remains frontend-only. Product behavior and experiment provenance remain governed by the parent repository's `docs/APPLICATION_STATE.md` and `docs/ADAPTER_RECOVERY_PLAN.md`. This refresh does not change backend behavior, model providers, training, serving or deployment.

## Colors

The palette connects cool graphite and pale titanium through one emerald family. Preserve the source OKLCH values rather than maintaining a parallel hex palette.

### Primary

- **Operational emerald** (`primary`, `primary-foreground`, `primary-soft`): primary actions, selections and focus-related emphasis in the light workspace.
- **Preview mint** (`preview-emerald`): the preserved hero emphasis, active workflow chapters, story outcomes and evidence actions on dark surfaces. It is intentionally brighter than operational emerald.

### Neutral

- **Graphite presentation** (`preview-bg`, `workflow-bg`, `preview-text`, `preview-muted`, `preview-line`): dark presentation canvas, text hierarchy and quiet dividers.
- **Graphite navigation** (`sidebar-graphite`, `sidebar-foreground`, `sidebar-accent`, `sidebar-border`): the desktop sidebar and its grouped destinations. The desktop background overrides the base sidebar token; the portaled mobile drawer retains the base sidebar treatment.
- **Titanium workspace** (`background`, `surface-satin`, `surface-glass`, `search-surface`): cool working canvas, restrained tinted surfaces and floating utility chrome.
- **Paper and separators** (`card`, `card-foreground`, `popover`, `popover-foreground`, `board-paper`, `board-lane`, `border`, `input`): readable cards, dialogs and grouped lanes.
- **Supporting states** (`secondary`, `muted`, `accent` and their foreground pairs): subdued controls, metadata and hover surfaces.

### Semantic states

Preserve the status foreground/background pairs. Active is blue; awaiting confirmation is amber; resolved is green; escalated is red; cancelled is gray. Urgency is a separate axis: emergency red, urgent orange, routine green, unknown gray. The purple pair remains available to existing auxiliary badges. Destructive actions use the dedicated destructive pair. The lane dots and portfolio distribution use their local chart colors; the accompanying labels carry the meaning.

**The Semantic Color Rule.** Keep status and urgency colors tied to their existing labels. Mint emphasis does not imply completion or model readiness.

## Typography

**Display Font:** Inter with a sans-serif fallback for the preview.
**Body Font:** Inter with UI sans-serif and system fallbacks for the workspace.

The pairing is one family with different density. Large, tightly tracked story headings establish the presentation; compact titles, tabular numerals and muted metadata keep working cards scannable. There is no distinct mono font in the approved surfaces.

### Hierarchy

- **Hero display:** the frontmatter `display` role is preserved. At widths up to 600px its size is 58px; the hero paragraph becomes 16px with a 1.7 line-height.
- **Workflow headline:** `headline-workflow`; at widths up to 650px it becomes 34px. The desktop short-height adjustment uses 40px where its media query applies.
- **Operations page title:** `title-operations`; 28px at widths up to 700px. The portfolio heading is 30px, weight 400, with a 1.2 line-height, and its metrics use `metric-portfolio` with tabular numerals.
- **Board title:** `title-board`; 14px at widths of at least 1500px and 15px at widths up to 700px. Metadata and tags are generally 10px on desktop and 11px on mobile. Lane headings move from 12px to 14px on mobile.
- **Attention inbox:** titles are 12px, weight 500, with a 1.45 line-height; metadata is 10px. Mobile raises these to 13px and 11px.
- **Narrative body:** `body-workflow`; 14px at widths up to 900px and 13px with a 1.6 line-height up to 650px. Evidence copy is 14px on desktop and 11px on mobile.
- **Shared workspace scale:** the actual CSS values are micro 0.75rem/1rem, body 0.875rem/1.4rem, strong 0.9375rem/1.5rem, section 1.0625rem/1.375rem, title 1.75rem/2.125rem and metric 1.625rem/1.875rem. At a 16px root these sizes are 12, 14, 15, 17, 28 and 26px. Some legacy inline comments describe older sizes; the declared values and component overrides are authoritative.
- **Labels:** grouped navigation uses uppercase `label-nav`; story labels are compact, quiet context. The mobile story's decorative model label and disclaimer use 8px locally; this is not a general text token.

**The Compact Hierarchy Rule.** Use the implemented surface hierarchy: the dashboard includes 10–13px metadata and card text, while narrative copy is larger. Do not claim a universal 14–16px minimum.

## Layout

The workspace keeps its shared maximum page container (110rem / 1760px), with 24px gutters, 28px at the extra-large breakpoint, and 16px on narrow mobile screens. The sticky desktop sidebar is 202px wide and scrolls vertically if its contents exceed the viewport. Below 1024px it becomes a modal navigation drawer (248px, capped at 82vw), with the same destinations, focus trapping, Escape close and focus return. Resizing to desktop closes the drawer.

The Maintenance deck is a three-column grid (1.05fr / 1.1fr / 0.85fr), with an 18px gap. At widths of at least 1500px it becomes 1.1fr / 1.2fr / 0.85fr with a 22px gap. At widths up to 1250px the visit rail spans a second row; at widths up to 700px all three panels stack. The board is four columns, two at 1250px and one at 700px. Lanes have independent overflow, with maximum card-stack heights of 660px, 550px at the middle breakpoint and 620px on mobile. The original list presentation, case actions, status filters, advanced filters and search remain available.

The preserved hero and preview navigation use a 1360px maximum container. The new story uses a 1600px maximum sticky stage and six equal chapter controls. Standard-height pages devote 650svh to the story, or 720svh at widths up to 650px, while the stage follows the viewport at 100svh. The desktop layout places copy beside the scene; narrow mobile stacks them. Normal scrolling updates the selected chapter, and chapter buttons can jump directly to a stage. The canvas does not capture pointer input or vertical scrolling.

At viewport heights of 650px or less, the story becomes normal document flow: automatic section height, relative stage positioning and visible overflow. The chapter controls move above the content and choose the stage directly. The short-and-narrow scene has a fixed 350px visual area. This height override is part of the responsive contract, including landscape screens.

## Elevation & Depth

Depth combines tonal layering, restrained ambient shadows and selective reflective materials. The metal portfolio panel and silver preview actions use directional gradients and inset highlights. Case cards stay opaque. The story evidence panel uses a translucent gradient with a 24px backdrop blur, while the utility bar uses a 20px blur. The complete gradients, borders and shadows are preserved in the sidecar snippets and the source stylesheets.

### Shadow Vocabulary

- **Card:** the root `shadow-card` provides a small contact shadow for standard working cards and primary controls.
- **Panel:** `shadow-panel` separates ordinary overlays; portaled popper surfaces use `shadow-floating` for a broader lift.
- **Board card:** a small contact shadow at rest, with a stronger shadow and a 2px rise on hover.
- **Portfolio:** a broad dark shadow plus a single inset top highlight gives the metal panel its mass.
- **Evidence glass:** a dark ambient shadow and inset highlight separate the glass from the 3D scene.

The precise values live in the sidecar's `extensions.shadows`; they are not color primitives. Focus uses the root ring color and the global 2px outline with a 4px offset. Shared buttons use their existing 2px ring with a 1px offset.

**The Material Boundary Rule.** Use glass for the illustrative evidence layer and floating chrome. Keep operational case content on opaque paper surfaces.

## Shapes

Use measured rounded rectangles: shared controls and cards follow the root radius scale, board cards and tags use the medium radius, large deck panels use the extra-large radius, and workflow evidence has its own intermediate radius. The frontmatter records these actual values. Small dots, avatars and status indicators may remain circular. Borders are thin and quiet; the board groups cards through a tinted lane rather than outlining every data item heavily. The portfolio emblem and 3D chip are signature material elements, not replacements for routine icons.

## Components

### Buttons

Workspace buttons are compact and responsive to press. Preserve the existing default, outline, ghost, destructive, secondary and link variants. The default size is 36px high; small and large sizes are 32px and 40px. Primary buttons use operational emerald; preview entry actions retain the silver gradient, at least 50px height and a small hover rise. Disabled buttons keep reduced opacity and no pointer actions. Use the existing focus and reduced-motion treatment; do not remove keyboard indication.

### Inputs and search

The global search is a quiet inset titanium field, 40px high and `min(440px, 50vw)` on desktop. It expands within the utility bar below the desktop breakpoint and becomes a full row on narrow screens. Preserve its accessible combobox label and real API-backed results across tickets, properties, tenants and contractors. Its Maintenance query also filters the loaded queue. Detached result panels and form dialogs use root semantic colors so they do not depend on a parent theme selector.

### Navigation

Group the eight existing destinations under Workspace, Portfolio and Analysis. Active links have an emerald-tinted metal gradient; ordinary links use pale sidebar text and a darker hover surface. The desktop link height is 41px, with 12px text. Preserve `aria-current`, real unread counts, signed-in operator identity and actual agent status. The mobile drawer remains scrollable and keeps the same destinations.

### Chips and state labels

Use visible words with the existing semantic foreground/background pairs. General pills inherit the shared label treatment; board tags intentionally override it to compact sizing and padding. Keep urgency separate from case state. Archival sample records stay explicitly marked. Empty, loading and error states state the actual condition instead of rendering decorative placeholder numbers.

### Operations deck and board

The portfolio panel reads API metrics, including active cases, awaiting confirmation and resolved this week. Its distribution is derived from actual counts. The attention inbox shows up to three escalations from the loaded, filtered queue, with that scope stated in its footer. The visit rail shows up to five upcoming confirmed visits from the API and labels the count as “shown,” not a portfolio total.

Board is the default view. Its lanes are Escalated, In progress, Confirming and Closed; Closed combines resolved and cancelled cases while preserving their individual state badges. Cards link to the case and retain the original action menu. Property imagery, assignment, urgency and updated time remain attached to the same API record. There is no drag-to-change-status behavior.

### Workflow story

The six chapters are Report, Coordinate, Review, Resolve, Learn and Evaluate. The house/scaffold assembly supports the repair sequence; the later chapters transform it into a layered metal chip. Glass evidence stays in the DOM beside the scene. The page contains no repair API query or mutation and does not run model calls while scrolling.

The scene is lazy-loaded when the story approaches the viewport. React Three Fiber uses demand rendering, a pixel-ratio range of 1–1.5, low-power WebGL preference and a one-frame environment capture. Scroll and resize invalidate the scene only while active; camera settling requests further frames only as needed. Once loaded, the scene remains mounted offscreen, while active scroll invalidation stops. Reduced motion snaps to the selected chapter and uses instant chapter scrolling. Diagram view, loading/error boundaries and the WebGL-unavailable message preserve access to the narrative.

The existing router owns route transitions. The new workflow uses scroll position and demand-rendered Three.js, not Motion-driven copy transitions. Existing global reduced-motion rules suppress animated route transitions and shorten control animation; board hover travel is explicitly removed. No new packages are introduced: the implementation uses the already installed Three.js 0.186.1, React Three Fiber 9.8.2 and Drei 10.7.9.

The Evaluate evidence is a dated local historical record from 24 October: the Qwen3-4B candidate scored 10/12 (83.3%) versus base-plus-prompt 5/12 (41.7%) in Mubit's internal evaluation. It is below the 85% target and the minimum of 20 judged cases. The page explicitly states that no adapter deployment is confirmed; these figures are not live serving results or an independent holdout benchmark. The story's repair events are illustrative, and physical demo events remain simulated.

## Do's and Don'ts

### Do:

- **Do** preserve the approved hero composition, copy, graphite palette, mint emphasis and silver actions.
- **Do** reuse root semantic tokens for portal menus, dialogs and other detached surfaces.
- **Do** preserve visible labels for status, urgency, loading, error, empty and archival-sample states.
- **Do** distinguish portfolio totals from loaded queue counts and visits shown.
- **Do** keep chapter controls, Diagram view and reduced-motion behavior available.
- **Do** keep historical evaluation evidence dated and separate from live serving status.

### Don't:

- **Don't** put real repair actions or model calls behind scrolling or the homepage story.
- **Don't** treat an agent proposal, approval, executed action, completed visit and resolved case as interchangeable.
- **Don't** restyle the approved hero through the workflow or operations stylesheets.
- **Don't** convert the compact dashboard into a universal typography rule for all surfaces.
- **Don't** describe the candidate adapter as ready, deployed or independently benchmarked on the strength of the historical internal evaluation.
- **Don't** add animation that blocks page scrolling or hides chapter controls on short screens.

## UI cleanup — 25 October 2026

Property History uses a fixed 1180px minimum table with narrow selection/navigation
columns, a 22% issue column, an 18% outcome column and right-aligned quotes. Two-line
previews open an inline, keyboard-operable full-record row; CSV exports retain the
original complete values. On smaller screens a labelled, focusable scroll region
contains the table. Full details stay within the reading viewport. Simulation
provenance remains visible when contractor names are clamped.

One labelled Trade/Year filter area replaces the repeated chart-adjacent chips.
Options come from the loaded history. TanStack Router owns filter/sort URL updates,
retains unrelated search values and restores state on back/forward. Search-only
updates do not animate the page or reset scrolling.

Shared cards can shrink within grids. Page actions wrap; property tabs use concise
labels; mobile property and tenant details wrap their content. Recent activity has
a keyboard-scrollable 640px reading area and no longer stretches the adjacent empty
appointments panel. Homepage art direction and the Maintenance board are unchanged.
The non-interactive workflow canvas wrapper ignores pointer events so its diagram
fallback cannot intercept chapter controls.

Maintenance's “In focus” values come from the existing dashboard-metrics hook and
its five-second polling: active, awaiting_confirmation, resolved_this_week and
total. They describe the portfolio, independently of the filtered/limited queue.
