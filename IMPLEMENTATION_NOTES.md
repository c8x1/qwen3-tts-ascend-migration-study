# Implementation Notes

## Current status

- Phase: Knowledge-site template
- Active task: Task 3 — independent sidebar state
- Last verified commit: `26e7bbb`

## Completed checkpoints

- Research design approved
- Template visual and interaction specification approved
- Fixed-dependency Playwright harness established and verified
- Semantic three-column page and local visual system implemented and verified

## Major decisions requiring user confirmation

- None. The template direction is approved.

## Conservative deviations

| ID | Date | Stage | Uncertainty | Conservative choice | Reason | Impact | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV-000 | 2026-07-16 | Template setup | No deviation recorded | Preserve approved specification | Initial state | None | New uncertainty discovered |
| DEV-001 | 2026-07-17 | Task 2 structure test | The supplied local-resource assertion referenced browser-global `location` from Playwright's Node.js test process | Derive the page origin with `new URL(page.url()).origin` before comparing resource URLs | Node.js has no global `location`; the supplied expression raised `ReferenceError` after the page was implemented | Test intent and production behavior are unchanged; local-only runtime resources remain enforced | Test runner gains a Node.js `location` global or the assertion moves fully into page context |

## Evidence gaps

- Sidebar behavior, responsive interaction, accessibility audit, print behavior, and visual baselines remain to be implemented or verified in later tasks.

## Next actions

1. Implement independent sidebar state.
2. Verify responsive, no-script, accessibility, print, and visual behavior.
