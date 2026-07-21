# Phase 3 Reference Walkthroughs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish evidence-backed walkthroughs of MindSpeed-MM, MindSpeed-LLM and MOSS-TTS plus a Qwen3-TTS-to-Ascend-910B migration mapping, without claiming a real NPU migration run.

**Architecture:** Preserve Phase 2 immutable indexes as the source-location layer. Add strict reference evidence and coverage contracts, render catalog pages deterministically, and reject missing, unclassified, non-fixed or hardware-overclaimed assertions.

**Tech Stack:** Python standard library, JSON/CSV, deterministic static HTML, Playwright, fixed-revision GitHub links and read-only source snapshots.

## Global Constraints

- MindSpeed-MM `0edd553e0ac9c912fe422c42cc9f42db9255ddcf` is main anchor; MindSpeed-LLM `434baff794bd5594ebc9ed8a5b399110da9a44f0` is text-scale satellite; MOSS-TTS `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` is speech/codec satellite.
- Qwen3-TTS target is `022e286b98fbec7e1e916cb940cdf532cd9f488e`.
- Preserve learning lane `torch-npu 2.7.1 + CANN 8.5.0` and validation lane `torch-npu 2.7.1 + CANN 8.5.2`; validation lane remains `pending_hardware` without real 910B proof.
- States are only `verified`, `project_claim`, `inference`, `pending_hardware`; every state has a visible textual label.
- Never track source bodies, source snapshots, weights, datasets, checkpoints, audio, credentials or absolute local paths.
- Never run CUDA/NPU/model/training/inference/evaluation/8-card/multi-node commands.
- Retain existing accessible collapsible three-column shell, offline/no-script/print behavior and deterministic output.

## File Map

| Path | Responsibility |
| --- | --- |
| `research/reference-evidence.json` | Fixed-revision source evidence and mapping assertions. |
| `research/reference-coverage.csv` | One coverage disposition for every declared reference surface. |
| `research/schemas/reference-*.schema.json` | Evidence and coverage schemas. |
| `scripts/phase3_contracts.py` | Reference evidence/range/state/coverage validators. |
| `content/reference-*.json` | Three reference walkthrough catalogs. |
| `content/migration-mapping.json` | Qwen3-TTS-to-Ascend lifecycle mapping catalog. |
| `scripts/site_builder.py`, `scripts/build_site.py` | Phase 3 loading, navigation, rendering and local search. |
| `scripts/validate_phase3.py` | Phase 2 + Phase 3 public production gate. |
| `tests/test_phase3_contracts.py` | Contract regression tests. |
| `tests/site/phase3-reference-mapping.spec.js` | Browser/accessibility/offline regression tests. |

### Task 1: Establish Phase 3 contracts

**Files:** Create `research/schemas/reference-evidence.schema.json`, `research/schemas/reference-coverage.schema.json`, `scripts/phase3_contracts.py`, `tests/test_phase3_contracts.py`.

**Interfaces:** `load_reference_evidence(path: Path) -> dict[str, ReferenceEvidence]`; `validate_reference_coverage(rows, indexes, evidence) -> list[str]`; `PHASE3_CATALOG_PATHS: tuple[Path, ...]`.

- [ ] Write failing `unittest` cases that reject duplicate IDs, unknown snapshots, non-materialized paths, invalid line ranges, invalid states, absolute/traversal paths, unconditioned `pending_hardware`, and duplicate/missing coverage dispositions.
- [ ] Run `python3 -m unittest tests.test_phase3_contracts -v`; expect `ModuleNotFoundError: scripts.phase3_contracts`.
- [ ] Implement frozen `ReferenceEvidence(evidence_id, snapshot_id, path, start_line, end_line, state, claim, source_ids, verification_condition)` and strict stdlib JSON/CSV validators that compare paths/ranges to Phase 2 indexes.
- [ ] Run `python3 -m unittest tests.test_phase3_contracts -v`; expect PASS.
- [ ] Commit only contract files with message `feat: add Phase 3 evidence contracts`.

### Task 2: Parallel source study — MindSpeed-MM

**Files:** Create ignored `.superpowers/sdd/phase3-mindspeed-mm-report.md`; append only conservative gaps to `IMPLEMENTATION_NOTES.md`.

**Interfaces:** Consumes the fixed MM snapshot/index and official documentation; produces at least 24 fixed path/line candidates spanning launch/config, data, model adapter, train/optimizer, NPU/distributed, checkpoint/restart, profiling/performance and diagnostics, each with state and Qwen3-TTS mapping note.

- [ ] Reconcile local fixed paths with official immutable URLs and record retrieval date/source type.
- [ ] Trace the eight surfaces with concise paraphrases; never include source bodies or execution claims.
- [ ] Record only static-versus-hardware uncertainties in notes.
- [ ] Run `rg -n '/Users/|source_root|BEGIN PRIVATE|token|T[O]DO|T[B]D' .superpowers/sdd/phase3-mindspeed-mm-report.md IMPLEMENTATION_NOTES.md`; expect no prohibited report content.

### Task 3: Parallel source study — MindSpeed-LLM

**Files:** Create ignored `.superpowers/sdd/phase3-mindspeed-llm-report.md`; append only conservative gaps to `IMPLEMENTATION_NOTES.md`.

**Interfaces:** Produces at least 20 fixed candidates for launch, parallel dimensions, communication, checkpoint/restart, profiling and single-node/multi-node operations, explicitly scoped to text-scale evidence.

- [ ] Locate entry scripts/configs and symbols through the index; preserve relative paths/ranges.
- [ ] For each parallel/recovery/performance point distinguish direct fact, official claim and Qwen3-TTS inference.
- [ ] Record that no topology, throughput or TTS equivalence is prescribed.
- [ ] Run `rg -n '/Users/|source_root|BEGIN PRIVATE|token|T[O]DO|T[B]D' .superpowers/sdd/phase3-mindspeed-llm-report.md IMPLEMENTATION_NOTES.md`; expect no prohibited report content.

### Task 4: Parallel source study — MOSS-TTS

**Files:** Create ignored `.superpowers/sdd/phase3-moss-tts-report.md`; append only conservative gaps to `IMPLEMENTATION_NOTES.md`.

**Interfaces:** Produces at least 16 fixed candidates for TTS entry, codec/model boundaries, data boundaries, training/inference interfaces and Qwen3-TTS contrasts; includes explicit restricted-asset exclusions.

- [ ] Trace source-only package/CLI, model/codec, data, train/infer and configuration surfaces; do not open/reproduce excluded audio or JSONL assets.
- [ ] Mark every comparison source-backed contrast or pending implementation/hardware question.
- [ ] Record that MOSS-TTS does not establish Ascend training readiness.
- [ ] Run `rg -n '/Users/|source_root|BEGIN PRIVATE|token|T[O]DO|T[B]D' .superpowers/sdd/phase3-moss-tts-report.md IMPLEMENTATION_NOTES.md`; expect no prohibited report content.

### Task 5: Integrate evidence, coverage and catalogs

**Files:** Create `research/reference-evidence.json`, `research/reference-coverage.csv`, `content/reference-mindspeed-mm.json`, `content/reference-mindspeed-llm.json`, `content/reference-moss-tts.json`, `content/migration-mapping.json`; modify `tests/test_phase3_contracts.py`, `IMPLEMENTATION_NOTES.md`.

**Interfaces:** Consumes Tasks 2–4 reports; produces at least 18 pages (6 MM, 4 LLM, 3 MOSS, 5 mapping) with fixed-location evidence.

- [ ] First add failing tests that require three reference snapshot IDs, a group per project, target-plus-reference evidence on each mapping page, and an observation/pass condition for every hardware-pending mapping.
- [ ] Convert reports into concise evidence: `verified` static facts, `project_claim` official documentation, `inference` cross-project mapping, `pending_hardware` 910B-only evidence.
- [ ] Create exactly one coverage disposition per surface and catalogs using current block types.
- [ ] Run `python3 -m unittest tests.test_phase3_contracts -v`; expect PASS.
- [ ] Commit data, catalogs, tests and notes with message `docs: add reference walkthrough evidence`.

### Task 6: Extend builder and validator

**Files:** Modify `research/schemas/page-catalog.schema.json`, `scripts/site_builder.py`, `scripts/build_site.py`, `tests/test_site_builder.py`; create `scripts/validate_phase3.py`.

**Interfaces:** Produces generated reference/mapping pages, search records, role-based navigation and a fail-closed validator.

- [ ] Add failing temporary-output tests for every `reference/*.html` and `mapping/*.html` slug, local-search title, relative navigation and unknown-evidence pre-write failure.
- [ ] Run `python3 -m unittest tests.test_site_builder -v`; expect failure before Phase 3 catalog loading exists.
- [ ] Extend slug schema to `reference/[a-z0-9-]+.html` and `mapping/[a-z0-9-]+.html`; merge target/reference evidence without collision; include all catalogs and navigation groups.
- [ ] Implement validator composition: Phase 2 gate, reference range/state/coverage checks, exact output membership, generated links/headings/ARIA, immutable links, public tracking; malformed inputs fail without traceback.
- [ ] Run `python3 -m unittest tests.test_site_builder tests.test_phase3_contracts -v && python3 scripts/validate_phase3.py`; expect PASS and zero omissions/broken links.
- [ ] Commit builder/validator files with message `feat: render Phase 3 walkthrough pages`.

### Task 7: Browser regression and final verification

**Files:** Create `tests/site/phase3-reference-mapping.spec.js`; regenerate `site/` via `python3 scripts/build_site.py`; update `IMPLEMENTATION_NOTES.md`.

- [ ] Write Playwright cases for visible state labels, immutable source links, local search across all groups, offline navigation, no-script chapters, desktop/mobile drawers, 200% reflow and axe WCAG A/AA.
- [ ] Run `npx playwright test tests/site/phase3-reference-mapping.spec.js --workers=1`; expect failure until generation support exists.
- [ ] Run `python3 scripts/build_site.py && npx playwright test tests/site/phase3-reference-mapping.spec.js --workers=1`; expect PASS.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py' -v && npm test && python3 scripts/validate_phase3.py && git diff --check`; expect all PASS and no public/local-path leak.
- [ ] Append exact counts and remaining hardware claims, then commit generated site/tests/notes with message `test: verify Phase 3 migration walkthrough`.

### Task 8: Independent review and publication readiness

**Files:** Create ignored `.superpowers/sdd/phase3-final-review.md`; modify only files implicated by findings.

- [ ] Produce `.superpowers/sdd/phase3-review.diff` from `git diff --find-renames $(git merge-base origin/main HEAD)..HEAD`.
- [ ] Review claim state, revision/range validity, coverage, leakage, migration overclaiming, accessibility and test adequacy.
- [ ] For each Critical/Important finding: add regression first, smallest fix, focused test plus `python3 scripts/validate_phase3.py`, then re-review.
- [ ] Run Task 7 final gates once more before any completion or push claim.
