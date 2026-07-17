# Implementation Notes

## Current status

- Phase: Knowledge-site template
- Active task: Task 3 review corrections — independent sidebar state
- Last verified baseline: `79bd13a`

## Completed checkpoints

- Research design approved
- Template visual and interaction specification approved
- Fixed-dependency Playwright harness established and verified
- Semantic three-column page and local visual system implemented and verified
- Task 2 review fixes verified: readable no-script tablet rail, semantic current-page state, visible active marker, and parsed-origin resource checks
- Independent desktop and laptop sidebar states implemented and verified
- Valid sidebar preferences persist independently; invalid values recover to viewport defaults
- `Alt+[` and `Alt+]` shortcuts toggle the canonical accessible sidebar buttons and keep `aria-expanded` synchronized
- Storage failures retain usable in-memory sidebar interaction across responsive breakpoint transitions for the current page view
- Task 3 review corrections verified: mobile triggers remain outside inert drawers, same-side activation closes, side switching is independent, and mode-specific labels stay synchronized
- Corrected Task 3 coverage: 9 sidebar tests, 14 combined structure/sidebar tests, and 15 current full-suite tests; the authorized completion total is 24 after Task 4 adds its unchanged 9 tests

## Major decisions requiring user confirmation

- None. The template direction is approved.

## Conservative deviations

| ID | Date | Stage | Uncertainty | Conservative choice | Reason | Impact | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV-000 | 2026-07-16 | Template setup | No deviation recorded | Preserve approved specification | Initial state | None | New uncertainty discovered |
| DEV-001 | 2026-07-17 | Task 2 structure test | The supplied local-resource assertion referenced browser-global `location` from Playwright's Node.js test process | Derive the page origin with `new URL(page.url()).origin` and compare parsed resource URL origins | Node.js has no global `location`; the supplied expression raised `ReferenceError` after the page was implemented | Test intent and production behavior are unchanged; local-only runtime resources remain enforced without prefix false positives | Test runner gains a Node.js `location` global or the assertion moves fully into page context |
| DEV-002 | 2026-07-17 | Task 2 review | The approved `721–1199px` default narrowed the right rail to `2.5rem` even when JavaScript was unavailable, leaving complete evidence content unreadable | Keep the no-script evidence rail at `15.3125rem` and scope the intermediate-width `2.5rem` default to `html.js`; retain all Task 3 data-attribute overrides | Progressive enhancement requires complete content to remain usable without JavaScript | No-script tablet users retain a readable evidence rail; enhanced pages can still apply the approved collapsed state | Task 3 changes its enhancement marker or intermediate-width state contract |
| DEV-003 | 2026-07-17 | Task 3 review | The approved markup nested canonical drawer triggers inside the nav/aside elements that become inert and offscreen when closed on mobile | Move both fixed-ID triggers into a sibling grid overlay outside the drawer containers while retaining their IDs, `aria-controls`, and desktop/laptop alignment | Descendants of an inert drawer cannot remain focusable or clickable, so an external canonical trigger is required to reopen it | Mobile triggers stay visible and operable while closed drawers remain inert; desktop and laptop controls retain their rail-edge positions | A future header/control redesign replaces the sibling overlay with an equally accessible external trigger location |

## Evidence gaps

- Mobile focus trapping, Escape/backdrop closure, responsive interaction beyond Task 3 open/close/switch coverage, accessibility audit, print behavior, and visual baselines remain to be verified in later tasks.

## Next actions

1. Verify remaining mobile focus management and responsive behavior.
2. Verify no-script, accessibility, print, and visual behavior.
