# Task 1 report: catalog and navigation contract

## Changed files

- `research/schemas/page-catalog.schema.json`
- `scripts/site_builder.py`
- `scripts/phase2_contracts.py`
- `scripts/validate_phase3.py`
- `tests/test_site_builder.py`
- `tests/test_phase2_contracts.py`
- `tests/site/phase2-navigation-search.spec.js`
- `tests/site/final-review-regressions.spec.js`
- Regenerated existing `site/**/*.html` surfaces (31 pages; no catalog content changed).

## TDD evidence

### RED

```sh
python -m unittest tests.test_site_builder.SiteBuilderTest.test_catalog_track_accepts_only_learning_route_tracks tests.test_site_builder.SiteBuilderTest.test_render_groups_navigation_and_marks_page_learning_track tests.test_phase2_contracts.GeneratedSiteContractTest.test_fixed_link_validation_uses_generated_catalog_page_count
```

Result: failed as expected: `track` was an unknown schema field, grouped navigation labels were absent, and `validate_fixed_links()` did not accept the generated catalog pages.

### GREEN

```sh
python -m unittest tests.test_site_builder.SiteBuilderTest.test_catalog_track_accepts_only_learning_route_tracks tests.test_site_builder.SiteBuilderTest.test_render_groups_navigation_and_marks_page_learning_track tests.test_phase2_contracts.GeneratedSiteContractTest.test_fixed_link_validation_uses_generated_catalog_page_count
npm test -- --grep "all Phase 3 pages are reachable through chapter navigation|chapter tree exposes the complete ordered path and current page"
```

Result: 3 Python tests passed; 2 Playwright tests passed.

## Final verification

```sh
python scripts/validate_phase3.py
npm test
```

`validate_phase3.py` passed: 4 indexes, 13 reference evidence records, 31 pages.

The full Playwright run passed 50 tests and failed the 3 approved visual-baseline snapshots (desktop, laptop, mobile) because grouped labels and lesson wayfinding intentionally change the page chrome. Snapshot renewal is left to the visual-review scope.

## Commit

`feat: add learning route navigation contract` (final commit SHA recorded in the task handoff).

## Concerns

- Existing catalogs deliberately omit `track` until Task 2. The builder treats those 31 pages as `源码深读`, while the schema validates any supplied `track` against the three allowed labels.
- No `content/learning-route-pilot.json` was created and no substantive tutorial catalog text was changed.
