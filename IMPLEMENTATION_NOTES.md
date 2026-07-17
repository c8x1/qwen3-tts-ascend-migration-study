# Implementation Notes

## Current status

- Phase: Knowledge-site template
- Active task: Second whole-branch review remediation complete
- Last verified baseline: Second whole-branch review remediation — 38/38 Playwright tests passed on 2026-07-17

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
- Whole-branch review remediation: collapsed icon rails now contain named, focusable destinations with visible hover/focus tooltips; no decorative-only controls remain
- Whole-branch review remediation: mobile retains the current chapter, a keyboard-operable search expander, and an explicit no-script chapter-index fallback
- Whole-branch review remediation: the representative chapter tree supports reusable nested disclosures, automatic current-path expansion, and keyboard operation
- Whole-branch review remediation: the source excerpt has success and failure copy paths, an immutable official MindSpeed commit/line link, adjacent-page navigation, semantic footer, and printable source/citation URLs
- Whole-branch review remediation: JavaScript-only controls are hidden by default and enabled only under `html.js`; complete navigation, tree content, article, evidence, links, search form, and fallback remain available without JavaScript
- Whole-branch review remediation: axe now audits every WCAG 2/2.1 A/AA violation at desktop, laptop, mobile-closed, and both mobile-drawer states; explicit edge fixtures cover long paths, nested navigation, empty evidence, missing page TOC, 200% reflow, and print references
- Official source provenance verified on 2026-07-17: `git ls-remote https://github.com/Ascend/MindSpeed.git HEAD` returned `b8d8b936f9793aa211baf88b6f501ccbc4aed02b`; the displayed content is sourced from `mindspeed/core/parallel_state.py` lines 424–445 at that commit with outer indentation normalized for the standalone excerpt
- Restricted-path audit expression corrected to match standalone `.env`, `.env.*`, restricted directories at any depth, and `.pem`/`.key` files
- Whole-branch completion verification: 37/37 Playwright tests passed; all three regenerated Chromium/Darwin snapshots passed zero-diff revalidation and were inspected at original resolution; `git diff --check` was clean
- Strict restricted-path audit verification: ten positive fixtures covering standalone/nested `.env*`, every restricted directory, `.pem`, and `.key` matched; the same expression found no tracked restricted path in this repository
- Second whole-branch review remediation: both collapsed rails now provide all eight specified destinations (`首页/章节/源码索引/迁移映射` and `目录/证据/警示/引用`), and geometry-based hover/focus assertions prove each tooltip retains non-zero painted area after every clipping ancestor and viewport intersection
- Second whole-branch review remediation: edge fixtures run complete WCAG A/AA axe analysis after injecting long paths/titles and deeper trees, removing the page TOC and evidence content/entries, and applying the 720 CSS-pixel reflow equivalent of a 1440-pixel window at 200% zoom
- Second whole-branch review remediation: adjacent-page links use distinct, stable relative template paths instead of placeholder hash targets
- Second whole-branch completion verification: 38/38 Playwright tests passed; desktop/laptop/mobile snapshots passed zero-diff revalidation and were inspected at original resolution; only the laptop pixels changed because its collapsed right rail now includes the required warning destination

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
| DEV-006 | 2026-07-17 | Whole-branch review source fixture | A moving branch name or illustrative hash would make the template's source evidence unverifiable over time | Resolve the official GitHub remote HEAD, pin the full `b8d8b936…` commit, fetch the raw file, and show only the exact 424–445 line range behind an immutable link | The template must teach evidence discipline and must not imply that a fabricated snippet is official source | The sample remains reproducible even as MindSpeed advances; it is explicitly a template fixture, not a claim that this is Qwen3-TTS's eventual migration hook | Phase 1 selects a different main reference project or replaces the template fixture with a research-backed page |
| DEV-007 | 2026-07-17 | Whole-branch review reflow test | CSS `zoom: 2` scales the document box itself and creates artificial overflow unlike browser 200% zoom, which halves the layout viewport | Exercise a 720 CSS-pixel viewport as the 200% reflow equivalent of a 1440 CSS-pixel window, open the real chapter drawer, and inject long paths plus a visibly painted sixth-level tree path | This tests WCAG-style reflow behavior without conflating page zoom CSS with browser zoom, while keeping the deep fixture observable rather than inert/offscreen | Automated coverage reflects the layout viewport users receive at 200%; physical/browser chrome is outside Playwright's page model | Cross-browser zoom automation becomes part of the project or a browser exposes stable zoom controls to Playwright |
| DEV-008 | 2026-07-17 | Second whole-branch review collapsed rails | Tooltip elements positioned outside a `2.5rem` rail cannot be painted through an ancestor whose overflow is clipped | Keep collapsed rail content minimal and set only the collapsed sidebar container to `overflow: visible`; retain scrollable overflow while expanded | The tooltip remains attached to its semantic link and can escape the rail without portals, duplicated controls, or remote/runtime dependencies | All eight hover/focus tooltips are visibly painted and keyboard focus retains the approved rail geometry | A future rail adds enough destinations to exceed the viewport height or introduces content other than the bounded shortcut list |

## Evidence gaps

- Axe covers automated WCAG A/AA rules across five responsive/drawer states; it does not replace manual assistive-technology testing.
- Visual regression coverage is intentionally limited to Chromium on Darwin at the three approved viewports.
- Print verification covers visibility under emulated print media, not physical-printer output or multi-page pagination details.
- The no-script search fallback leads to the complete chapter index; a future multi-page content build still needs a generated static search index or server-backed search.

## Next actions

1. Begin Phase 1 reference-project research using the approved reference-selection design.
