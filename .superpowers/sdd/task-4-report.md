# Phase 1 Task 4 Report — Ascend Candidate Breadth Research

## Status

**DONE_WITH_CONCERNS**

- Commit: `0ab639055401fbff1239bdf78b6584b0fe3261c1`
- Subject: `research: map Ascend training candidate landscape`
- Branch: `agent/phase1-reference-selection`
- Push: not performed, as instructed
- Site/Playwright: no site files changed; Playwright not run because Task 4 is research-only

The tracked Task 4 artifacts are complete and verified. The concerns are explicit evidence boundaries: MindSpeed aggregate-license vendoring risk, unknown CANN 8.5.2 patch compatibility, no verified exact-Qwen3-TTS multi-node run, and no public exact-Qwen3-TTS pretraining recipe.

## Delivered artifacts

1. `research/candidate-landscape.md` — 187-line breadth report with all eight required sections plus qualification screening.
2. `research/source-ledger.csv` — 47 total sources: 17 inherited official Qwen sources and 30 Task 4 additions (`SRC-018`–`SRC-047`).
3. `research/search-log.csv` — 38 total exact query rows: 11 inherited Task 3 rows and 27 Task 4 additions (`QRY-012`–`QRY-038`).
4. `research/candidates.csv` — 15 deduplicated canonical candidates: 4 shortlisted, 4 discovered, 7 rejected.
5. `IMPLEMENTATION_NOTES.md` — Task 4 status, checkpoints, DEC-001, DEV-016–019, evidence gaps and Task 5 handoff.

No weights, datasets, checkpoints or candidate source trees were downloaded, cloned or vendored.

## Search coverage and count discipline

The formal log covers all nine required query families:

- QRY-012: `Qwen3-TTS Ascend 910B training`
- QRY-013: `Qwen TTS MindSpeed training Ascend`
- QRY-014: `speech generation TTS Ascend 910B training`
- QRY-015: `audio tokenizer codec Ascend training`
- QRY-016: `Qwen3 MindSpeed multi-node training`
- QRY-017: `PyTorch TTS torch-npu distributed training`
- QRY-018: `Qwen 语音 合成 昇腾 训练`
- QRY-019: `Qwen3-TTS 昇腾 910B 训练`
- QRY-020: `MindSpeed 语音生成 多机训练`

Required channels are represented by exact rows for Huawei GitCode/hiascend, GitHub Web/API/fixed source, Gitee, ModelScope, Hugging Face and general Chinese/English Web search. Source/config/test/license/commit inspection is represented by fixed direct evidence in `SRC-019`–`SRC-047`.

Each Task 4 row has a unique numeric ID and timezone-aware ISO 8601 timestamp. Web counts are the number of unique tool-visible returned items, explicitly not search-engine totals. GitHub API rows record the API's exact `total_count`: QRY-035/036/037 are 1/0/0 with `incomplete_results=false`. QRY-038 preserves HTTP 401 with observable result count 0 and is excluded from saturation. Handoff searches that lacked exact reproducible counts were not fabricated into the tracked log.

## Saturation proof

All required channels were logged before two consecutive zero-new-candidate passes:

| Pass | Query IDs | Visible items | New eligible canonical repos |
| --- | --- | ---: | ---: |
| 1 | QRY-027–030 | 17 + 16 + 12 + 12 | 0 |
| 2 | QRY-031–034 | 3 + 12 + 15 + 17 | 0 |

Pass 1 strengthened known CAND-001 source evidence and retained the CANN 8.5.2/pretraining gaps. Pass 2 returned known CAND-001 speech paths, CAND-003 upstream, model cards or non-speech material. MOSS-TTS/CosyVoice3 paths inside CAND-001 were not duplicated as separate Ascend candidates. QRY-038 did not count toward either pass.

The conclusion is public-search saturation under the recorded method, not exhaustive Internet coverage.

## Candidate pool

- Total: 15
- Shortlisted: 4
- Discovered/not shortlisted: 4
- Rejected: 7
- Duplicate numeric IDs: 0
- Duplicate canonical URLs: 0
- Rejected entries without an explicit reason: 0

The final completeness correction added CAND-015 OpenMOSS/MOSS-Audio-Tokenizer as `rejected`: its fixed tree contains modeling, demo, ONNX and TensorRT paths but no public optimizer/backward/launch/config/checkpoint training lifecycle. This satisfies the requirement to retain plausible canonical inference/export projects rather than silently omit them.

## Shortlist

| ID | Role | Preliminary score | Fixed revision | License boundary |
| --- | --- | ---: | --- | --- |
| CAND-001 Ascend/MindSpeed-MM | exact Qwen3-TTS SFT main-reference candidate | 90 | `0edd553e0ac9c912fe422c42cc9f42db9255ddcf` | `Other`, aggregate BSD-3-Clause-style notices |
| CAND-002 Ascend/MindSpeed-LLM | text-Qwen3 pretraining/scale satellite | 82 | `434baff794bd5594ebc9ed8a5b399110da9a44f0` | `Other`, aggregate BSD-3-Clause-style notices |
| CAND-003 OpenMOSS/MOSS-TTS | speech/codec architecture satellite | 60 | `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` | Apache-2.0 |
| CAND-004 FunAudioLLM/CosyVoice | speech preprocessing/training satellite | 51 | `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` | Apache-2.0 |

CAND-001 establishes exact Qwen3-TTS **SFT**, not exact pretraining. CAND-002 establishes Qwen3 text-model scale engineering, not speech support. CAND-003/CAND-004 have Ascend score 0; their Ascend ports live in CAND-001 and were not counted twice.

## Training-chain boundaries

- CAND-001 evidence chain: Qwen3-TTS launcher → `torchrun`/HCCL/NPU → trainer/TrainEngine → forward/loss/`backward()` → AdamW/clip/step/scheduler/zero-grad → YAML FSDP/iteration/save config → DCP checkpoint/convert → ST baseline (`SRC-020`–`SRC-023`, `SRC-043`).
- CAND-002 evidence chain: Qwen3 launcher/config → `pretrain_gpt.py` forward/loss entry → training lifecycle backward/optimizer/scheduler → checkpoint save/load/resume (`SRC-027`, `SRC-044`–`SRC-046`).
- CAND-003/CAND-004 fixed upstream training entries establish speech training, but no upstream Ascend implementation (`SRC-030`–`SRC-033`).
- Inference/export-only items remain rejected even if they mention 910B, NPU patches, model training history or deployment support.

## Verification evidence

Fresh final gate after the CAND-015 correction and notes update:

```text
$ python3 scripts/validate_research.py
research data valid

$ python3 -m unittest tests/test_validate_research.py -v
Ran 15 tests in 0.077s
OK

$ rg -n "Search coverage|Search saturation|Candidate categories|Preliminary score|Rejection table|Shortlist|Coverage gaps|Source index" research/candidate-landscape.md
5:## Search coverage
33:## Search saturation
50:## Candidate categories
104:## Preliminary score
126:## Rejection table
140:## Shortlist
149:## Coverage gaps
161:## Source index

$ custom count/duplicate/score/evidence/fixed-revision/saturation audit
audit counts: 47 sources, 38 queries, 15 candidates
duplicate audit: clean
score/evidence audit: clean
shortlist/rejection/fixed-revision audit: 4/7, clean
saturation audit: 2 passes x 4 queries, clean

$ git diff --check / git diff --cached --check
no output; exit 0

$ no-site audit
clean

$ no-weight/data audit
clean

$ pycache cleanup
clean

$ staged-scope audit
only IMPLEMENTATION_NOTES.md and the four Task 4 research files; clean

$ post-commit git status --short
no output
```

No Playwright command was run.

## Deviations and concerns

1. **DEC-001 / major license risk:** MindSpeed-MM and MindSpeed-LLM root license texts aggregate BSD-3-Clause-style terms and upstream/file-level notices while repository metadata does not supply a reliable single SPDX classification. Both are conservatively `Other`. This phase stores metadata/links only. Clone/vendor/copy requires a later explicit user decision after file-level review.
2. **CANN 8.5.2 unknown:** CAND-001 documentation targets 8.5.0; CAND-002 current release route is 9.x with some 8.5.0 compatibility material. No inspected official source gives an exact 8.5.2 + PyTorch 2.7.1 row. Patch compatibility was not inferred.
3. **Multi-node run unknown:** CAND-001 exposes exact Qwen3-TTS multi-node parameters, but no model-specific multi-node run artifact was verified. CAND-002 scale evidence is not speech evidence. No candidate multi-node run was reproduced.
4. **Exact pretraining gap:** no public exact-Qwen3-TTS pretraining/DPO/GSPO/tokenizer-training recipe was found. CAND-002 only supplies adjacent Qwen3 scale engineering.
5. **Moving-only rejections:** CAND-006 and CAND-011–014 have official exclusion evidence but not all expose stable public commit permalinks verified in scope; revisions remain blank instead of guessed.
6. **Search limitation:** QRY-038 failed with HTTP 401; private, deleted, unindexed and access-controlled projects remain outside observable coverage.
7. **Historical/stale projects:** ModelZoo-PyTorch speech, WavTokenizer and broad ESPnet paths require finer Task 5-style review before any present-environment reuse claim.

## Task 5 handoff

Deep-audit CAND-001 and CAND-002 end to end. Audit only target-module-relevant speech/codec paths in CAND-003/CAND-004, keeping CAND-001's NPU/FSDP2 ports as the sole Ascend attribution. Preserve CANN 8.5.2 and multi-node execution as unknown until official compatibility or scoped hardware evidence exists. Do not clone/vendor MindSpeed sources until DEC-001 is resolved.

## Review remediation — 2026-07-17

### Status and commits

**DONE_WITH_CONCERNS**

- Remediation data commit: `16f3790072a1e923eac3de7ff6a7633e72fa6c44`
- Remediation base: `0ab639055401fbff1239bdf78b6584b0fe3261c1`
- Push: not performed
- Site/Playwright: no site file changed; Playwright was not run
- Weights/data: none downloaded, cloned, vendored or committed

### Findings remediated

1. **Complete 54-cell matrix.** QRY-012–020 preserve the nine general-Web family rows; QRY-039–083 add the other 45 Huawei-official, GitHub, Gitee, ModelScope and Hugging Face cells. Native GitHub API rows retain exact `total_count`; filtered-Web rows explicitly limit counts to tool-visible items.
2. **Discovery provenance.** QRY-084–089 replay the omitted searches for CAND-004, CAND-005, CAND-009, CAND-012, CAND-013 and CAND-014, with all six `accepted_ids` populated.
3. **Maintenance screening.** The landscape now records canonical project, fixed/latest meaningful SHA or explicit unknown, commit date, subject/release context, maintenance judgment and source for all 18 current candidates. This covers the 15 findings candidates plus three candidates discovered during the required rerun.
4. **Canonical/mirror correction.** CAND-005 now uses authoritative `https://gitcode.com/Ascend/ModelZoo-PyTorch` at `c9d4e7dc8a951fb9365e5ebe42601b0101d34ba3`; GitHub `6a2804a358a5b18e3dac1ab902f41f88e240b00f` remains fixed mirror evidence, and equivalence is explicitly unknown.
5. **Saturation restarted honestly.** QRY-092–093 added CAND-016 Inworld TTS and CAND-017 Alibaba unified-audio. QRY-097 then added CAND-018 official GLM-TTS and merged `prchbzy/glmtts-910b` as inference-only derivative evidence. Each discovery reset the counter. Only after the 18-candidate canonical/maintenance audit did QRY-104–112 and QRY-113–121 form two new consecutive 9-family passes: both were successful native API passes with `incomplete_results=false`, and neither added an eligible canonical repository. No failed or auth-gated query contributes zero-result evidence.

Final tracked counts are 64 sources, 121 exact query rows and 18 deduplicated candidates. The shortlist remains CAND-001–004: CAND-016/CAND-017 have no Ascend training evidence, while CAND-018's fixed GRPO entry hardcodes CUDA and its official/derivative NPU material establishes inference only.

### Fresh verification evidence

```text
$ python3 scripts/validate_research.py
research data valid

$ python3 -m unittest tests/test_validate_research.py -v
Ran 15 tests in 0.091s
OK

$ rg -n "Search coverage|Search saturation|Candidate categories|Preliminary score|Rejection table|Shortlist|Coverage gaps|Source index" research/candidate-landscape.md
all eight required sections found

$ matrix/provenance/maintenance/canonical/CAND-005/two-new-pass/count audit
matrix 54/54
provenance 6/6
maintenance/canonical 18/18 + 18/18
CAND-005 authoritative canonical plus fixed mirror relation clean
QRY-104–112: 9/9 successful, visible 0, new 0
QRY-113–121: 9/9 successful, visible 12, new 0
counts 64 sources / 121 queries / 18 candidates

$ git diff --check / git diff --cached --check
clean

$ no-site audit from 0ab6390
clean

$ no-weight/data path and >10 MiB file audits
clean

$ pycache cleanup and re-audit
clean
```

### Remaining concerns and limitations

1. Final saturation is bounded to the recorded public channels and the two native GitHub repository-search passes; private, deleted, unindexed and access-controlled projects remain unobservable.
2. Huawei/Gitee/ModelScope/Hugging Face matrix cells use exact domain-filtered fallbacks where no stable native search contract was available; their counts are tool-visible items, not platform totals.
3. DEC-001 remains unresolved: MindSpeed aggregate/file-level licensing still prohibits cloning or vendoring without a separate user-approved compliance decision.
4. No evidence closes the CANN 8.5.2 compatibility, exact Qwen3-TTS pretraining, or model-specific multi-node execution gaps.
5. CAND-016–018 improve breadth but do not change the shortlist or establish Ascend training; any Task 5 promotion requires fixed-source deep audit and, for NPU claims, scoped hardware evidence.
