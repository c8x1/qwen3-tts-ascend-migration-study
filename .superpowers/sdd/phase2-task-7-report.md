# Phase 2 Task 7 Report: Official Target SFT Walkthrough

## Outcome

Task 7 is complete. The generated knowledge site now contains 13 ordered HTML pages and 47,504 metadata-only search documents. The four new official-target walkthroughs are:

- `target/sft-data-collate.html` (order 7)
- `target/sft-training-loop.html` (order 8)
- `target/optimizer-checkpoint-export.html` (order 9)
- `target/coverage-gaps.html` (order 10)

The catalog records the official 12Hz Base single-speaker recipe, JSONL/offline-code and collate contracts, the source-ordered SFT embedding/forward/loss flow, Accelerate ownership boundaries, AdamW/export behavior, and the absence of a resumable optimizer/RNG checkpoint in the fixed tree. The coverage page emits all 35 CSV dispositions exactly once as 35 physical `data-coverage-path` lines.

No CUDA, NPU, training, inference, evaluation, or hardware command was run. No candidate implementation or migration mapping was added. Browser/Playwright validation remains deferred to Task 8 as required.

## Factual discipline

- Every new official-source link uses fixed Qwen3-TTS revision `022e286b98fbec7e1e916cb940cdf532cd9f488e`; the four pages contain no moving `main` link.
- Verified, inference, project-claim, and pending-hardware statements remain separate.
- `accelerate-ownership` limits its `TGT-TRAIN-001` verified paragraph to the objects passed through `accelerator.prepare`; wrapper transparency, process-local global state, and runtime sharding stay inference/pending.
- The embedding chain follows the fixed source order: speaker/text/codec-0 embeddings, speaker-slot write, text+codec-0 merge, residual embedding lookup, mask, then residual addition.
- The custom-speaker verified paragraph contains only the config rewrite, speaker row 3000, speaker-encoder removal, embedding injection, and safetensors write supported by `TGT-EXPORT-001`.
- The coverage CSV-to-catalog-to-renderer chain is explicitly labeled audit/build provenance and “非官方 Qwen3-TTS 调用链”.
- The project-native 2.7.1/CANN 8.5.0 lane is not called reproduced. The target 2.7.1/CANN 8.5.2 lane remains compatibility `unknown` and hardware pending.

## TDD record

RED was observed before implementation:

1. The exact brief test `test_full_catalog_has_thirteen_pages_and_required_training_sections` failed with `FileNotFoundError: content/target-training.json`.
2. The coverage-renderer fixture initially failed with `AssertionError: 0 != 35` before the narrowly derived `data-coverage-path` attribute existed.
3. Line-audit regressions were separately exposed for archive display labels, adjacent sections, index rows, and the inline search-data list before the approved formatting adaptations were implemented.
4. Independent review caught that the initial coverage assertion counted occurrences rather than physical lines. The strengthened regression failed with `AssertionError: 1 != 35` before `_render_table` joined coverage rows with newlines.
5. The same review cycle added exact source-order assertions for the embedding chain, evidence-range assertions for the verified ownership paragraph, and explicit non-runtime labeling for the coverage provenance chain; all failed against the pre-review catalog and passed after correction.

The final focused review-regression run passed four tests covering those issues.

## Approved generator and foundation adaptations

- `_render_table` derives `data-coverage-path` only when the section ID is `target-coverage` and the first header is exactly `path`; values still pass through the existing HTML escaping path. Only that table joins rows with newlines.
- Generated sections and generated source-index rows are separated by a single newline so line-oriented audits cannot cross unrelated DOM records.
- A non-empty top-level search-data list is serialized as one compact, sorted, script-safe object per line. JSON content and order are unchanged, and `<`, `>`, and `&` remain escaped so an embedded value cannot close the script element.
- Foundation provenance display labels now show `MindSpeed-MM (mindspeed-mm-0edd553e)` and `MindSpeed-LLM (mindspeed-llm-434baff7)` while preserving snapshot IDs, roles, and `codeload archive` acquisition semantics.

These adaptations were limited to satisfying the exact line-oriented audit contracts; generated HTML and search artifacts were rebuilt only through `scripts/build_site.py`.

## Verification evidence

- Focused post-review regressions: 4 tests, all passed.
- `python3 -m unittest tests.test_site_builder -q`: 29 tests, all passed.
- `python3 -m unittest tests.test_phase2_contracts tests.test_site_builder tests.test_source_index tests.test_validate_research -q`: 95 tests, all passed in 40.415 seconds.
- Explicit generator: `built 13 pages and 47504 search documents`.
- Exact Step 5 audit was run with fail-fast shell semantics:
  - 35 physical lines containing `data-coverage-path=`;
  - both MindSpeed archives labeled `codeload archive`;
  - zero matching archive rows labeled `clone`;
  - all three required boundary literals present.
- Two independent temporary builds each produced exactly 14 generator artifacts (13 HTML pages plus one search index). Their 14 SHA-256 hashes matched, and every fresh artifact matched the checked-in `site/` counterpart byte-for-byte.
- Generated navigation orders are exactly 1–13; all tested local links, fragments, and page IDs resolve uniquely.
- The external search index and inline search JSON parse to the same ordered 47,504-document list.
- `git diff --check` passed.

## Independent review

The required reviewer reported no critical issue. The initial review raised three important corrections and one minor clarification: physical coverage-line counting, exact embedding source order, evidence-range discipline in verified paragraphs, and provenance-vs-runtime labeling. All four were addressed with failing regression tests before production changes and are included in the passing verification above.

## Deferred interfaces

The page records, but does not implement, later work for full reference walkthroughs, CUDA-to-NPU migration mapping, import/device checks, operator/numerics and loss parity, audio/codec execution, checkpoint/inference validation, 8-card and multi-node behavior, and quality evaluation.
