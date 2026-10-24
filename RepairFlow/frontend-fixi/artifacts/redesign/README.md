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
