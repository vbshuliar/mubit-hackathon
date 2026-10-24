# Latest Fixi redesign captures

The current interface uses six scroll-linked chapters and a default repair board.
The following captures were produced through read-only browser verification on
25 October 2026; they show illustrative or existing simulated records.

| Current surface | Capture |
|---|---|
| Preserved hero, 1280×720 | [View](scroll-story/hero-desktop.png) |
| Repair workflow, 1280×720 | [View](scroll-story/story-desktop.png) |
| Mubit adapter chapter, 1280×720 | [View](scroll-story/mubit-desktop.png) |
| Repair board, desktop | [View](scroll-story/dashboard-desktop.png) |
| Repair board, mobile | [View](scroll-story/dashboard-mobile.png) |
| Workflow, 390×844 | [View](scroll-story/story-mobile.png) |
| Mubit chapter, 390×844 | [View](scroll-story/mubit-mobile.png) |
| Short portrait controls, 390×600 | [View](scroll-story/story-short-portrait.png) |
| Landscape controls, 844×390 | [View](scroll-story/story-short-landscape.png) |

See [current verification](../../docs/REDESIGN_VERIFICATION.md).

---

## Earlier iteration (historical)

The images below predate the scroll story and board; retain them for comparison.
The capture script selectors have been updated, but the script was not rerun for
the latest iteration.

# Fixi redesign captures

Captured from the working frontend at desktop (1440×1000), tablet (768×1024) and mobile (390×844). API writes were blocked. The homepage was captured with API access blocked entirely.

| Surface | Desktop | Mobile | Tablet |
|---|---|---|---|
| Homepage | [View](homepage-desktop.png) | [View](homepage-mobile.png) | [View](homepage-tablet.png) |
| Walkthrough | [View](walkthrough-desktop.png) | [View](walkthrough-mobile.png) | [View](walkthrough-tablet.png) |
| Maintenance | [View](maintenance-desktop.png) | [View](maintenance-mobile.png) | [View](maintenance-tablet.png) |
| Case | [View](case-desktop.png) | [View](case-mobile.png) | [View](case-tablet.png) |
| Overview | [View](overview-desktop.png) | [View](overview-mobile.png) | [View](overview-tablet.png) |

The initial review found cramped mobile case progress and slight toolbar/tab overflow. The confirmation captures show a vertical mobile rail, wrapping controls and no horizontal page overflow. The mobile product preview uses a responsive workspace capture.

See [verification notes](../../docs/REDESIGN_VERIFICATION.md) for checks and inherited limitations. `npm run capture:redesign` reproduces captures against `http://localhost:5174`; set `FIXI_PREVIEW_URL` to target another frontend. Chrome is required.
