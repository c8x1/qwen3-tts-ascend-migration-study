# Implementation Notes

## Current status

- Phase: Knowledge-site template
- Active task: Template Tasks 1–4 complete
- Last verified baseline: Task 4 completion working tree — 24/24 Playwright tests passed on 2026-07-17

## Completed checkpoints

- Research design approved
- Template visual and interaction specification approved
- Task 1 complete: fixed-dependency Playwright harness established and verified
- Task 2 complete: semantic three-column page and local visual system implemented and verified
- Task 2 review fixes verified: readable no-script tablet rail, semantic current-page state, visible active marker, and parsed-origin resource checks
- Independent desktop and laptop sidebar states implemented and verified
- Valid sidebar preferences persist independently; invalid values recover to viewport defaults
- `Alt+[` and `Alt+]` shortcuts toggle the canonical accessible sidebar buttons and keep `aria-expanded` synchronized
- Storage failures retain usable in-memory sidebar interaction across responsive breakpoint transitions for the current page view
- Task 3 review corrections verified: mobile triggers remain outside inert drawers, same-side activation closes, side switching is independent, and mode-specific labels stay synchronized
- Task 3 complete: 9 sidebar tests verify independent state, persistence, failure recovery, breakpoint transitions, shortcuts, and mobile drawer operation
- Task 4 complete: 6 responsive/accessibility tests verify focus containment and restoration, saved-preference isolation, no-JavaScript content, axe serious/critical findings, print visibility, and narrow-screen overflow
- Task 4 visual baselines complete: desktop (1440×900), laptop (1024×768), and mobile (390×844) Chromium/Darwin snapshots were inspected, tracked, and reverified without diff
- Exact completion result: 24 Playwright tests passed; `git diff --check` and the restricted-path audit were clean

## Major decisions requiring user confirmation

- None. The template direction is approved.

## Conservative deviations

| ID | Date | Stage | Uncertainty | Conservative choice | Reason | Impact | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV-000 | 2026-07-16 | Template setup | No deviation recorded | Preserve approved specification | Initial state | None | New uncertainty discovered |
| DEV-001 | 2026-07-17 | Task 2 structure test | The supplied local-resource assertion referenced browser-global `location` from Playwright's Node.js test process | Derive the page origin with `new URL(page.url()).origin` and compare parsed resource URL origins | Node.js has no global `location`; the supplied expression raised `ReferenceError` after the page was implemented | Test intent and production behavior are unchanged; local-only runtime resources remain enforced without prefix false positives | Test runner gains a Node.js `location` global or the assertion moves fully into page context |
| DEV-002 | 2026-07-17 | Task 2 review | The approved `721–1199px` default narrowed the right rail to `2.5rem` even when JavaScript was unavailable, leaving complete evidence content unreadable | Keep the no-script evidence rail at `15.3125rem` and scope the intermediate-width `2.5rem` default to `html.js`; retain all Task 3 data-attribute overrides | Progressive enhancement requires complete content to remain usable without JavaScript | No-script tablet users retain a readable evidence rail; enhanced pages can still apply the approved collapsed state | Task 3 changes its enhancement marker or intermediate-width state contract |
| DEV-003 | 2026-07-17 | Task 3 review | The approved markup nested canonical drawer triggers inside the nav/aside elements that become inert and offscreen when closed on mobile | Move both fixed-ID triggers into a sibling grid overlay outside the drawer containers while retaining their IDs, `aria-controls`, and desktop/laptop alignment | Descendants of an inert drawer cannot remain focusable or clickable, so an external canonical trigger is required to reopen it | Mobile triggers stay visible and operable while closed drawers remain inert; desktop and laptop controls retain their rail-edge positions | A future header/control redesign replaces the sibling overlay with an equally accessible external trigger location |
| DEV-004 | 2026-07-17 | Task 4 accessibility | The approved gold token `#9b6c29` produced 3.68:1 contrast for small navigation labels on `#eee5d8`, below the axe-enforced WCAG AA 4.5:1 threshold | Darken only `--gold` to `#76521f` | Preserve the approved warm palette while clearing the exact serious color-contrast violation without weakening axe | Navigation labels remain visually gold-brown and pass the serious/critical axe audit | Typography or navigation background changes alter the measured contrast |
| DEV-005 | 2026-07-17 | Task 4 snapshot tooling | With Playwright 1.61.1, bare `--update-snapshots` consumes the following test path as its optional mode and rejects it | Set the package script to `playwright test --update-snapshots=all` | Keep `npm run test:update-snapshots -- tests/site/template-visual.spec.js` executable with explicit, current CLI semantics | The approved update command generates all three requested baselines and the subsequent normal run verifies zero diff | Playwright removes the optional-mode ambiguity or the project changes snapshot-update policy |

## Evidence gaps

- Axe covers automated serious/critical rules on the desktop template; it does not replace manual assistive-technology testing.
- Visual regression coverage is intentionally limited to Chromium on Darwin at the three approved viewports.
- Print verification covers visibility under emulated print media, not physical-printer output or multi-page pagination details.

## Next actions

1. Begin Phase 1 reference-project research using the approved reference-selection design.
