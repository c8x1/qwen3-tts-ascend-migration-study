# Learning Route Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a three-page, beginner-facing learning-route pilot while retaining all 31 evidence walkthrough pages and their verification guarantees.

**Architecture:** Extend the catalog schema with a navigation track, make the builder render grouped static navigation and lesson wayfinding, then add two catalog pages and replace the existing home content with the route map. Generated pages remain static and evidence-driven.

**Tech Stack:** Python static-site builder, JSON Schema/catalogs, Playwright, unittest.

## Global Constraints

- Keep all 31 existing walkthrough slugs, local search behavior, no-JS reading, and immutable evidence links.
- Add exactly two new generated pages: `guide/migration-boundary.html` and `guide/implementation-route.html`; the rewritten home is the third pilot surface.
- Navigation groups are exactly `入门教程`, `源码深读`, and `实施路线`.
- New runtime conclusions remain `pending_hardware`; do not run CUDA, NPU, model, training, inference, or evaluation workloads.

---

### Task 1: Catalog and navigation contract

**Files:**
- Modify: `research/schemas/page-catalog.schema.json`, `scripts/site_builder.py`, `scripts/phase2_contracts.py`, `scripts/validate_phase3.py`
- Modify: `tests/test_site_builder.py`, `tests/test_phase3_contracts.py`, `tests/site/phase2-navigation-search.spec.js`, `tests/site/final-review-regressions.spec.js`

- [ ] Write tests that require valid `track` values, three grouped navigation labels, all pages reachable, and fixed-link validation sized from the generated catalog.
- [ ] Run focused tests and verify they fail because the schema/builder lacks tracks and guide pages.
- [ ] Add the `track` catalog field, grouped static navigation, per-page wayfinding rendering, and count-driven fixed-link validation.
- [ ] Run focused unit and browser tests; commit `feat: add learning route navigation contract`.

### Task 2: Three pilot surfaces

**Files:**
- Modify: `content/site-foundation.json`, `content/target-architecture.json`, `content/target-training.json`, `content/reference-mindspeed-mm.json`, `content/reference-mindspeed-llm.json`, `content/reference-moss-tts.json`, `content/migration-mapping.json`
- Create: `content/learning-route-pilot.json`
- Modify: `scripts/build_site.py`, `scripts/validate_phase3.py`, `IMPLEMENTATION_NOTES.md`
- Test: `tests/test_site_builder.py`, `tests/site/learning-route-pilot.spec.js`

- [ ] Write tests for the two exact guide slugs, 33 total generated pages, lesson wayfinding, route-stage labels, offline search inclusion, and no-JS readability.
- [ ] Run focused tests and verify they fail because the guide catalog is absent.
- [ ] Assign tracks to all catalogs; add the route map to home; add the two tutorial pages with scoped evidence/`pending_hardware` boundaries; register the catalog and document the scope in implementation notes.
- [ ] Build the site, run focused tests, and commit `feat: add learning route pilot pages`.

### Task 3: Whole-site verification and review

**Files:**
- Modify only if verification/review identifies a defect.

- [ ] Run Phase 3 validation, Python tests, and the full Playwright suite.
- [ ] Request a task review, fix critical or important findings, then repeat affected checks.
- [ ] Commit any verified review fix and publish the tested branch under the user-approved repository workflow.
