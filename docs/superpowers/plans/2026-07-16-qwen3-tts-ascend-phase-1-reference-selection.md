# Qwen3-TTS Ascend 参考项目选型 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可审计的研究基础设施，完成 Qwen3-TTS 官方目标基线、Ascend 训练候选项目全网发现与深度审计，并提交主参考项目和专项参考项目的选型决策包。

**Architecture:** 第一阶段以 CSV 证据台账和 Markdown 审计报告为事实源，使用 Python 标准库校验字段、枚举、评分与证据引用。研究流程先固定目标架构，再广搜候选、缩小名单、逐仓库审计，最后在主项目这个重大决策点暂停并请求用户确认；确认后才能按固定 commit 制定知识站与源码走读的下一阶段计划。

**Tech Stack:** Git/GitHub、Python 3 标准库、`unittest`、CSV、Markdown、GitHub/Gitee/ModelScope/Hugging Face 与官方文档检索。

## Global Constraints

- 目标硬件是华为 Ascend 910B 系列。
- 当前环境基线是 CANN 8.5.2 与 PyTorch 2.7.1，但允许为项目兼容性推荐其他环境。
- 研究覆盖预训练、SFT、推理验证、单机 8 卡与多机多卡。
- 规模化路线允许并优先采用 MindSpeed/MindSpeed-LLM，不把纯 torch-npu 最小迁移作为主路线。
- 本阶段只研究、获取和走读成熟参考项目，不修改 Qwen3-TTS 训练源码，不宣称完成 910B 真机验证。
- 默认不下载模型权重、训练数据集或其他大体积非必要产物。
- 关键结论必须标记为“已证实”“项目声明”“分析推断”或“待真机验证”。
- 关键来源使用 S/A/B/C 等级；C 级来源只能发现线索，不能单独支撑关键结论。
- 持续维护根目录 `IMPLEMENTATION_NOTES.md`；每个任务完成后、每次提交前更新当前进度、证据缺口和偏差项。
- 会改变主项目、技术路线、许可处理或核心结论的重大不确定性必须暂停询问用户。
- 不改变大方向的细节不确定性采用保守方案，并记录到 `IMPLEMENTATION_NOTES.md` 的“保守偏差项”，不逐项打断用户。
- 每个可审阅节点提交到 `main` 并推送到公开仓库；不得提交密钥、令牌、本机信息、权重、数据集或许可证禁止再分发的内容。

---

## Phase Boundary

本计划只覆盖第一阶段“候选研究与选型”。主项目名称、源码布局和固定 revision 尚未由证据确定，因此知识站实现、主项目逐文件走读和迁移映射分别在用户确认选型后制定后续计划。第一阶段本身可以独立验收：它交付完整检索记录、候选审计、可复算评分和明确的选型建议。

### Task 1: 建立研究治理与持续记录

**Files:**
- Create: `README.md`
- Create: `IMPLEMENTATION_NOTES.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-07-16-qwen3-tts-ascend-reference-research-design.md`
- Produces: 所有后续任务使用的项目入口、进展记录格式、偏差记录格式和敏感内容排除规则。

- [ ] **Step 1: 验证治理文件尚未建立**

Run:

```bash
test ! -e README.md && test ! -e IMPLEMENTATION_NOTES.md
```

Expected: exit 0。

- [ ] **Step 2: 写入项目入口说明**

Create `README.md` with these exact sections and facts:

```markdown
# Qwen3-TTS → Ascend 910B Migration Study

本仓库系统研究 Qwen3-TTS 训练工程从 NVIDIA GPU 迁移到华为 Ascend 910B 所需的成熟参考项目、Ascend 训练知识和源码映射。

## Current phase

Phase 1: official baseline, candidate discovery, source audit, and reference-project selection.

## Deliverables

- `research/`: search logs, evidence ledger, candidate scores, and audit reports
- `docs/superpowers/specs/`: approved design specifications
- `docs/superpowers/plans/`: executable phase plans
- `site/`: multi-page Chinese learning site, created after reference selection

## Evidence policy

Every material claim is labeled as verified fact, project claim, analysis inference, or pending Ascend 910B validation. Secondary articles may discover leads but cannot independently support a critical conclusion.

## Scope boundary

This repository studies existing migration projects. It does not claim that Qwen3-TTS training has been ported or validated on Ascend 910B.
```

- [ ] **Step 3: 写入持续进展与偏差记录**

Create `IMPLEMENTATION_NOTES.md` with this initial content:

```markdown
# Implementation Notes

## Current status

- Phase: Phase 1 — reference-project research and selection
- Active task: Task 1 — research governance
- Last verified commit: design commit `bc1f672`

## Completed checkpoints

- Approved research and knowledge-site design
- Public GitHub repository initialized

## Major decisions requiring user confirmation

- Main reference project and satellite-project combination, after candidate audit

## Conservative deviations

| ID | Date | Stage | Uncertainty | Conservative choice | Reason | Impact | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEV-000 | 2026-07-16 | Governance | No deviation recorded | Preserve current scope | Initial state | None | New uncertainty discovered |

## Evidence gaps

- No candidate project has been audited yet.
- No Ascend 910B runtime claim has been independently validated.

## Next actions

1. Establish evidence data contracts and validation.
2. Reconstruct the Qwen3-TTS official target baseline.
3. Discover and audit Ascend training candidates.
```

- [ ] **Step 4: 扩展公开仓库忽略规则**

Append these exact rules to `.gitignore` while preserving `.superpowers/`:

```gitignore
.env
.env.*
*.pem
*.key
__pycache__/
*.pyc
.pytest_cache/
models/
weights/
datasets/
checkpoints/
```

- [ ] **Step 5: 验证治理内容和忽略规则**

Run:

```bash
rg -n "Current phase|Evidence policy|Scope boundary" README.md
rg -n "Current status|Major decisions requiring user confirmation|Conservative deviations|Evidence gaps|Next actions" IMPLEMENTATION_NOTES.md
git check-ignore .superpowers/example .env models/example.bin datasets/example.json checkpoints/step-1.pt
git diff --check
```

Expected: README 命中 3 行；notes 命中 5 个章节；四类敏感或大体积路径均被忽略；`git diff --check` 无输出且 exit 0。

- [ ] **Step 6: 记录并推送治理提交**

```bash
git add README.md IMPLEMENTATION_NOTES.md .gitignore
git commit -m "chore: establish research governance"
git push origin main
```

Expected: commit 成功，`main` 推送成功。

### Task 2: 建立证据数据契约与自动校验

**Files:**
- Create: `research/methodology.md`
- Create: `research/source-ledger.csv`
- Create: `research/search-log.csv`
- Create: `research/candidates.csv`
- Create: `scripts/validate_research.py`
- Create: `tests/test_validate_research.py`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: 设计规格中的评分、来源等级和结论状态。
- Produces: `validate_research(root: pathlib.Path) -> list[str]`；后续任务写入的三份 CSV；统一研究方法。

- [ ] **Step 1: 先写校验器测试**

Create `tests/test_validate_research.py`:

```python
import csv
import tempfile
import unittest
from pathlib import Path

from scripts.validate_research import validate_research


SOURCE_HEADER = [
    "source_id", "title", "url", "publisher", "source_grade",
    "accessed_at", "used_for", "archive_status",
]
SEARCH_HEADER = [
    "query_id", "channel", "query", "run_at", "result_count",
    "accepted_ids", "notes",
]
CANDIDATE_HEADER = [
    "candidate_id", "name", "url", "revision", "license",
    "ascend_completeness", "architecture_proximity", "scale_maturity",
    "reproducibility", "docs_license", "total", "status",
    "evidence_ids", "exclusion_reason",
]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


class ValidateResearchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        research = self.root / "research"
        research.mkdir()
        write_csv(
            research / "source-ledger.csv",
            SOURCE_HEADER,
            [["SRC-001", "Official source", "https://example.com/doc", "Vendor", "S", "2026-07-16", "training support", "live"]],
        )
        write_csv(research / "search-log.csv", SEARCH_HEADER, [])
        write_csv(
            research / "candidates.csv",
            CANDIDATE_HEADER,
            [["CAND-001", "Example", "https://example.com/repo", "abc123", "Apache-2.0", "25", "20", "15", "12", "8", "80", "audited", "SRC-001", ""]],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_research_data_has_no_errors(self) -> None:
        self.assertEqual(validate_research(self.root), [])

    def test_score_total_must_equal_dimensions(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = list(csv.reader(path.open(encoding="utf-8")))
        rows[1][10] = "81"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("CAND-001: total 81 does not equal 80", validate_research(self.root))

    def test_source_grade_must_be_known(self) -> None:
        path = self.root / "research" / "source-ledger.csv"
        rows = list(csv.reader(path.open(encoding="utf-8")))
        rows[1][4] = "Z"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("SRC-001: invalid source_grade Z", validate_research(self.root))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认因实现缺失而失败**

Run:

```bash
python3 -m unittest tests/test_validate_research.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validate_research'`.

- [ ] **Step 3: 实现最小但完整的数据校验器**

Create `scripts/validate_research.py`:

```python
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


SOURCE_HEADER = [
    "source_id", "title", "url", "publisher", "source_grade",
    "accessed_at", "used_for", "archive_status",
]
SEARCH_HEADER = [
    "query_id", "channel", "query", "run_at", "result_count",
    "accepted_ids", "notes",
]
CANDIDATE_HEADER = [
    "candidate_id", "name", "url", "revision", "license",
    "ascend_completeness", "architecture_proximity", "scale_maturity",
    "reproducibility", "docs_license", "total", "status",
    "evidence_ids", "exclusion_reason",
]
SCORE_LIMITS = {
    "ascend_completeness": 30,
    "architecture_proximity": 25,
    "scale_maturity": 20,
    "reproducibility": 15,
    "docs_license": 10,
}
SOURCE_GRADES = {"S", "A", "B", "C"}
ARCHIVE_STATES = {"live", "mirror", "unavailable"}
CANDIDATE_STATES = {"discovered", "shortlisted", "audited", "rejected", "recommended"}


def read_rows(path: Path, expected_header: list[str], errors: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            errors.append(f"{path}: invalid header")
            return []
        return list(reader)


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_research(root: Path) -> list[str]:
    errors: list[str] = []
    research = root / "research"
    sources = read_rows(research / "source-ledger.csv", SOURCE_HEADER, errors)
    read_rows(research / "search-log.csv", SEARCH_HEADER, errors)
    candidates = read_rows(research / "candidates.csv", CANDIDATE_HEADER, errors)

    source_ids: set[str] = set()
    for row in sources:
        source_id = row["source_id"]
        if not source_id or source_id in source_ids:
            errors.append(f"duplicate or empty source_id: {source_id}")
        source_ids.add(source_id)
        if row["source_grade"] not in SOURCE_GRADES:
            errors.append(f"{source_id}: invalid source_grade {row['source_grade']}")
        if row["archive_status"] not in ARCHIVE_STATES:
            errors.append(f"{source_id}: invalid archive_status {row['archive_status']}")
        if not valid_url(row["url"]):
            errors.append(f"{source_id}: invalid URL {row['url']}")
        try:
            date.fromisoformat(row["accessed_at"])
        except ValueError:
            errors.append(f"{source_id}: invalid accessed_at {row['accessed_at']}")

    candidate_ids: set[str] = set()
    for row in candidates:
        candidate_id = row["candidate_id"]
        if not candidate_id or candidate_id in candidate_ids:
            errors.append(f"duplicate or empty candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        if row["status"] not in CANDIDATE_STATES:
            errors.append(f"{candidate_id}: invalid status {row['status']}")
        if not valid_url(row["url"]):
            errors.append(f"{candidate_id}: invalid URL {row['url']}")

        scores: dict[str, int] = {}
        for field, maximum in SCORE_LIMITS.items():
            try:
                value = int(row[field])
            except ValueError:
                errors.append(f"{candidate_id}: {field} is not an integer")
                value = 0
            if not 0 <= value <= maximum:
                errors.append(f"{candidate_id}: {field} {value} outside 0..{maximum}")
            scores[field] = value
        expected_total = sum(scores.values())
        try:
            total = int(row["total"])
        except ValueError:
            errors.append(f"{candidate_id}: total is not an integer")
            total = -1
        if total != expected_total:
            errors.append(f"{candidate_id}: total {total} does not equal {expected_total}")

        for source_id in filter(None, row["evidence_ids"].split("|")):
            if source_id not in source_ids:
                errors.append(f"{candidate_id}: unknown evidence_id {source_id}")

    return errors


def main() -> int:
    errors = validate_research(Path.cwd())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("research data valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 运行单元测试并确认通过**

Run:

```bash
python3 -m unittest tests/test_validate_research.py -v
```

Expected: 3 tests, all `ok`, final status `OK`.

- [ ] **Step 5: 建立真实研究文件和方法说明**

Create the three CSV files with exactly these header rows:

```csv
source_id,title,url,publisher,source_grade,accessed_at,used_for,archive_status
```

```csv
query_id,channel,query,run_at,result_count,accepted_ids,notes
```

```csv
candidate_id,name,url,revision,license,ascend_completeness,architecture_proximity,scale_maturity,reproducibility,docs_license,total,status,evidence_ids,exclusion_reason
```

Create `research/methodology.md` with sections covering: channel inventory, exact query logging, inclusion rules, exclusion rules, S/A/B/C source levels, four claim states, the 30/25/20/15/10 score rubric, duplicate handling, fixed-revision policy, license policy, search saturation rule, and major-decision escalation. The search saturation rule is: all required channels have been queried and two consecutive query-family passes add no new eligible candidate.

- [ ] **Step 6: 验证真实研究骨架**

Run:

```bash
python3 scripts/validate_research.py
python3 -m unittest tests/test_validate_research.py -v
git diff --check
```

Expected: `research data valid`; 3 tests pass; whitespace check has no output.

- [ ] **Step 7: 更新 notes 并提交推送**

Set `Active task` to Task 2, add evidence contracts and validator to completed checkpoints, and set the next action to the official Qwen3-TTS baseline. Record any conservative file-format choice as a deviation.

```bash
git add IMPLEMENTATION_NOTES.md research scripts/validate_research.py tests/test_validate_research.py
git commit -m "feat: add auditable research data contracts"
git push origin main
```

Expected: commit and push succeed.

### Task 3: 重建 Qwen3-TTS 官方目标基线

**Files:**
- Create: `research/target/qwen3-tts-official-baseline.md`
- Modify: `research/source-ledger.csv`
- Modify: `research/search-log.csv`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: 官方 Qwen 源码、官方模型页、官方技术报告及对应固定 revision。
- Produces: 候选评分中的架构接近度基准；后续迁移映射使用的目标模块清单。

- [ ] **Step 1: 执行官方优先检索并逐条记录**

Run these query families against official Qwen/Alibaba domains first, then GitHub repository search for the official organization:

```text
Qwen3-TTS official GitHub training
Qwen3-TTS official technical report architecture
Qwen3-TTS official ModelScope training fine-tuning
Qwen3-TTS official Hugging Face model card
Qwen3-TTS CUDA NCCL flash attention training
```

For every query, append one row to `research/search-log.csv`. For every source used, append one row to `research/source-ledger.csv` with access date, source grade, purpose, and availability. Do not use an unofficial tutorial to establish an architectural fact when an official source exists.

- [ ] **Step 2: 固定官方源码版本并建立目标报告**

Create `research/target/qwen3-tts-official-baseline.md` with these sections:

1. Official artifacts and fixed revisions
2. Released model variants and training-related claims
3. Repository map and whether training code is public
4. End-to-end data and control flow
5. Text and audio tokenization or codec path
6. Model components and generation stages
7. Pretraining, SFT, inference, and evaluation entry points
8. CUDA, NCCL, fused-kernel, mixed-precision, and custom-extension dependencies
9. Single-node and multi-node assumptions
10. Confirmed facts, project claims, analysis inferences, and unknowns
11. Target-module checklist for future migration mapping
12. Source index using `SRC-*` identifiers

Each factual paragraph must end with at least one `SRC-*` source identifier. If official training code is absent, state that fact and identify exactly which training details remain unknowable from public artifacts.

- [ ] **Step 3: 核对官方基线的可追溯性**

Run:

```bash
python3 scripts/validate_research.py
rg -n "Official artifacts|Repository map|End-to-end|CUDA|Confirmed facts|Target-module checklist|Source index" research/target/qwen3-tts-official-baseline.md
rg -n "SRC-[0-9]+" research/target/qwen3-tts-official-baseline.md
git diff --check
```

Expected: CSV validation succeeds; all required report sections are present; source identifiers occur throughout the report; no whitespace errors.

- [ ] **Step 4: 更新 notes，记录目标侧未知项并提交推送**

Move unresolved official-code gaps into `Evidence gaps`. Any conservative interpretation of unpublished training details goes into `Conservative deviations` and must remain labeled as inference.

```bash
git add IMPLEMENTATION_NOTES.md research/target/qwen3-tts-official-baseline.md research/source-ledger.csv research/search-log.csv
git commit -m "research: establish Qwen3-TTS official baseline"
git push origin main
```

Expected: commit and push succeed.

### Task 4: 完成 Ascend 候选项目广度检索

**Files:**
- Create: `research/candidate-landscape.md`
- Modify: `research/source-ledger.csv`
- Modify: `research/search-log.csv`
- Modify: `research/candidates.csv`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: Task 3 的目标模块清单和 Task 2 的研究方法。
- Produces: 去重候选池、初步排除项和进入深度审计的短名单。

- [ ] **Step 1: 按渠道执行完整查询矩阵**

Use these query families in English and Chinese across Huawei official sources, GitHub, Gitee, ModelScope, Hugging Face, and general web search:

```text
Qwen3-TTS Ascend 910B training
Qwen TTS MindSpeed training Ascend
speech generation TTS Ascend 910B training
audio tokenizer codec Ascend training
Qwen3 MindSpeed multi-node training
PyTorch TTS torch-npu distributed training
Qwen 语音 合成 昇腾 训练
Qwen3-TTS 昇腾 910B 训练
MindSpeed 语音生成 多机训练
```

Record every executed query in `search-log.csv`, including zero-result searches. Add every plausible code project to `candidates.csv`; inference-only projects remain in the ledger with `rejected` status and an explicit exclusion reason.

- [ ] **Step 2: 去重并执行资格初筛**

For each candidate, verify canonical repository, owner, training-code presence, Ascend code presence, license, latest meaningful commit, supported model family, single-node or multi-node support, and documentation. Merge mirrors into the canonical candidate and preserve mirror URLs as sources. Never infer 910B training support from an NPU inference example.

- [ ] **Step 3: 形成候选地形报告**

Create `research/candidate-landscape.md` with:

1. Search coverage by channel and query family
2. Search saturation evidence
3. Candidate categories: direct match, architecture-near, Ascend-training-mature, speech-specialist, rejected
4. Preliminary score table
5. Rejection table with explicit reasons
6. Shortlist of three to five projects for source-level audit
7. Coverage gaps and conflicting claims
8. Source index

Stop broad discovery only when all required channels are logged and two consecutive query-family passes add no new eligible candidate. If the stop condition is not met, continue discovery rather than declaring coverage complete.

- [ ] **Step 4: 验证广度研究产物**

Run:

```bash
python3 scripts/validate_research.py
rg -n "Search coverage|Search saturation|Candidate categories|Preliminary score|Rejection table|Shortlist|Coverage gaps|Source index" research/candidate-landscape.md
git diff --check
```

Expected: CSV validation succeeds; all landscape sections exist; no whitespace errors.

- [ ] **Step 5: 更新 notes 并提交推送**

Record any inaccessible repositories, ambiguous licenses, stale-version assumptions, and conservative exclusions as evidence gaps or deviations. A license ambiguity that could affect local vendoring is a major decision and must be raised immediately.

```bash
git add IMPLEMENTATION_NOTES.md research/candidate-landscape.md research/source-ledger.csv research/search-log.csv research/candidates.csv
git commit -m "research: map Ascend training candidate landscape"
git push origin main
```

Expected: commit and push succeed.

### Task 5: 对短名单执行源码级深度审计

**Files:**
- Create: `research/candidate-audits.md`
- Modify: `research/source-ledger.csv`
- Modify: `research/candidates.csv`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: Task 4 的三至五个短名单项目。
- Produces: 每个评分维度均可追溯到源码或文档的统一候选审计报告。

- [ ] **Step 1: 固定每个短名单仓库的审计 revision**

For each candidate, resolve canonical remote, default branch, full commit SHA, commit date, license file, submodules, release tags, dependency manifests, and training entry points. Record these as S/A/B evidence rows before assigning deep-audit scores. Do not download weights or datasets.

- [ ] **Step 2: 逐项目完成统一源码审计卡**

Create `research/candidate-audits.md` with one `## Candidate: project-name` section per shortlist entry. Every candidate section must contain:

1. Identity, canonical URL, fixed SHA, license, and maintenance status
2. Claimed scope versus code-confirmed scope
3. Repository tree and training entry points
4. Ascend device initialization and torch-npu integration
5. MindSpeed/MindSpeed-LLM integration
6. Operator, mixed-precision, and custom-extension handling
7. Data pipeline and audio-specific coverage
8. DDP, TP, PP, CP, ZeRO, single-node, and multi-node coverage
9. Checkpoint, conversion, resume, inference, and evaluation
10. Environment and version matrix
11. Reproduction evidence and missing evidence
12. Score rationale for all five dimensions
13. Reusable knowledge for Qwen3-TTS
14. Non-transferable assumptions and risks
15. Source index and claim-state summary

Every nonzero score must cite at least one source ID. README claims without supporting code remain “project claim”.

- [ ] **Step 3: 复算评分并交叉比较**

Update `research/candidates.csv` with audited scores, fixed revisions, licenses, statuses, evidence IDs, and totals. Compare the top candidates against the Qwen3-TTS target-module checklist, not only against each other.

- [ ] **Step 4: 验证深度审计一致性**

Run:

```bash
python3 scripts/validate_research.py
count=$(rg -c '^## Candidate:' research/candidate-audits.md); test "$count" -ge 3 && test "$count" -le 5
rg -n "Score rationale|Reusable knowledge|Source index" research/candidate-audits.md
git diff --check
```

Expected: CSV validation succeeds; the report contains three to five candidate sections and the required audit subsections; no whitespace errors.

- [ ] **Step 5: 更新 notes 并提交推送**

Record all conservative scoring decisions and missing runtime evidence. If two leading candidates are within five points but imply materially different learning routes, flag the tie as a major decision rather than resolving it silently.

```bash
git add IMPLEMENTATION_NOTES.md research/candidate-audits.md research/source-ledger.csv research/candidates.csv
git commit -m "research: audit shortlisted Ascend projects"
git push origin main
```

Expected: commit and push succeed.

### Task 6: 发布选型决策包并请求重大决策确认

**Files:**
- Create: `research/reference-selection-proposal.md`
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: 官方目标基线、候选地形、深度审计卡和可复算评分。
- Produces: 一个主参考项目、少量专项参考项目和明确缺口的用户决策包。

- [ ] **Step 1: 编写选型建议**

Create `research/reference-selection-proposal.md` with:

1. Executive recommendation
2. Ranked audited candidates and final scores
3. Recommended main project with fixed SHA
4. Recommended training-scale satellite project
5. Recommended speech or codec satellite project when evidence shows a real gap
6. Qwen3-TTS target-module coverage matrix
7. What the combination covers and does not cover
8. Environment compatibility summary for project-native versions, CANN 8.5.2/PyTorch 2.7.1, and the recommended environment
9. License and local-source acquisition implications
10. Verified facts, project claims, inferences, and 910B validation gaps
11. Alternatives and consequences of choosing each
12. Exact next-stage scope after approval
13. Source index

The executive recommendation must state whether an exact public Qwen3-TTS-to-Ascend training project exists. If none is verifiable, say so directly and explain why the proposed combination is the closest defensible reference.

- [ ] **Step 2: 验证选型包覆盖关键决策**

Run:

```bash
python3 scripts/validate_research.py
rg -n "Executive recommendation|Recommended main project|coverage matrix|Environment compatibility|License|validation gaps|Alternatives|next-stage scope|Source index" research/reference-selection-proposal.md
git diff --check
```

Expected: research data validates; all decision sections exist; no whitespace errors.

- [ ] **Step 3: 更新 notes 并提交提案**

Set `Active task` to the selection gate. Put the main-project choice under `Major decisions requiring user confirmation`; summarize conservative scoring deviations and unresolved evidence gaps.

```bash
git add IMPLEMENTATION_NOTES.md research/reference-selection-proposal.md
git commit -m "research: propose Ascend reference project selection"
git push origin main
```

Expected: proposal is visible on the public repository.

- [ ] **Step 4: 向用户提交重大决策，而不是自行越过**

Present the recommended main project, satellites, fixed revisions, total scores, decisive evidence, gaps, license consequences, and two credible alternatives. Ask the user to approve or change the combination. Do not clone the selected repositories into `references/` and do not begin the knowledge-site implementation before the user decides.

Expected: explicit user approval or requested revision.

### Task 7: 固化用户选型并准备下一阶段

**Files:**
- Modify: `research/reference-selection-proposal.md`
- Modify: `research/candidates.csv`
- Modify: `IMPLEMENTATION_NOTES.md`
- Create: `research/selected-revisions.csv`

**Interfaces:**
- Consumes: 用户对主项目和专项项目组合的明确决定。
- Produces: 后续获取源码与逐文件走读计划使用的不可变仓库清单。

- [ ] **Step 1: 记录批准结果和固定 revision**

Add an `Approved selection` section to the proposal containing the decision date, selected roles, canonical URLs, full commit SHAs, licenses, and the user's requested changes. Mark the approved main project as `recommended` in `research/candidates.csv`.

Create `research/selected-revisions.csv` with this header and one row per approved repository:

```csv
role,candidate_id,name,canonical_url,revision,license,acquisition_policy
```

`acquisition_policy` must be `clone`, `submodule`, or `metadata-only`, selected from license and repository-size evidence. Use `metadata-only` conservatively when redistribution permission is unclear, and record that choice as a deviation.

- [ ] **Step 2: 验证选型记录**

Run:

```bash
python3 scripts/validate_research.py
python3 - <<'PY'
import csv
from pathlib import Path

path = Path("research/selected-revisions.csv")
rows = list(csv.DictReader(path.open(encoding="utf-8")))
assert rows, "selected-revisions.csv has no selected repository"
assert {row["acquisition_policy"] for row in rows} <= {"clone", "submodule", "metadata-only"}
assert all(len(row["revision"]) == 40 for row in rows if row["acquisition_policy"] != "metadata-only")
print(f"selected revisions valid: {len(rows)}")
PY
git diff --check
```

Expected: research validation succeeds; at least one selected repository exists; every cloned revision is a full 40-character SHA; no whitespace errors.

- [ ] **Step 3: 更新 notes 并提交推送**

Move the selection from major pending decisions to completed checkpoints. Set next actions to source acquisition and the phase-2 plan. Preserve every rejected alternative and deviation for final user review.

```bash
git add IMPLEMENTATION_NOTES.md research/reference-selection-proposal.md research/candidates.csv research/selected-revisions.csv
git commit -m "research: record approved reference selection"
git push origin main
```

Expected: approved selection is committed and pushed.

- [ ] **Step 4: 为下一阶段重新进入计划流程**

Use the approved `research/selected-revisions.csv` and the actual repository trees to write the next plan for source acquisition, local indexing, knowledge-site foundation, and Qwen3-TTS target walkthrough. That plan must use exact selected repository paths and must not assume files that were not verified at the fixed revisions.

Expected: a separately reviewable phase-2 implementation plan, grounded in the approved repositories.

## Phase 1 Completion Checks

Run all of the following immediately before claiming Phase 1 complete:

```bash
python3 -m unittest tests/test_validate_research.py -v
python3 scripts/validate_research.py
git diff --check
git status -sb
git log --oneline --decorate -8
git ls-remote origin refs/heads/main
```

Required evidence:

- All validator tests pass.
- Research CSV validation prints `research data valid`.
- Whitespace check has no output.
- Local `main` is clean and tracks `origin/main`.
- Remote `main` resolves to the same commit as local `HEAD`.
- `IMPLEMENTATION_NOTES.md` contains current status, completed checkpoints, major decisions, conservative deviations, evidence gaps, and next actions.
- No model weight, dataset, checkpoint, credential, or restricted source tree is tracked.
