# Phase 4 Task 2 report

- Added the deterministic 33-page learning-route pilot: the rewritten home route map, `guide/migration-boundary.html` (order 2, 入门教程), and `guide/implementation-route.html` (order 33, 实施路线).
- Assigned 入门教程 to the 14 foundation/official-target pages and 源码深读 to all 18 retained reference and mapping walkthroughs. The implementation page contains 环境、单卡、单机多卡、多机、性能、验收 as `pending_hardware` experiment stages; no runtime claims were introduced.
- Registered the pilot catalog, regenerated the site/search index, and intentionally regenerated the three visual baselines because the grouped navigation and home content changed chrome.

Verification run:

- `python3 scripts/build_site.py` — built 33 pages and 47,524 search documents.
- `python3 -m unittest tests.test_site_builder.SiteBuilderTest.test_phase3_catalogs_load_and_build_with_reference_evidence` — passed.
- `npx playwright test tests/site/learning-route-pilot.spec.js tests/site/template-visual.spec.js` — 5 passed.
- Visual snapshots were inspected at desktop resolution after regeneration.

No CUDA, NPU, model, training, inference, evaluation, or performance workload was run.

Implementation commit: `ac1070e9ac4d46aa27bc331e7737da6437ff44b4`
