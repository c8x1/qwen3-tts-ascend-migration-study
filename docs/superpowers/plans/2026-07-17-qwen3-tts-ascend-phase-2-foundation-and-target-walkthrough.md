# Qwen3-TTS Ascend Phase 2 Foundation and Target Walkthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立四个固定源码快照的可复现元数据索引，并在既有静态站模板上发布一组从 PyTorch 单卡基础出发、证据可追溯的 Qwen3-TTS 官方目标侧多页源码走读。

**Architecture:** 一个只依赖 Python 标准库的索引器从显式 `--source-root` 读取只读目录，以注册表中的 snapshot/revision/acquisition metadata 校验身份，输出不含绝对路径或源码正文的稳定 JSON。另一个标准库生成器把结构化页面内容、证据记录、覆盖矩阵和这些索引渲染为复用现有 `site/index.html`、`site/assets/{theme.css,layout.css,app.js}` 交互契约的多页静态站；Python 验证器和 Playwright 共同守住可追溯、无遗漏、离线、导航、搜索、ARIA 与响应式边界。

**Tech Stack:** Python 3.11+ 标准库（`argparse`、`ast`、`csv`、`hashlib`、`html`、`json`、`pathlib`、`tomllib`、`unittest`、`html.parser`）、HTML5、CSS3、原生 ES modules、Node.js 24、Playwright 1.61.1、axe-core Playwright 4.12.1。

## Global Constraints

- 本阶段只做索引基础、Qwen3-TTS 官方目标侧走读和静态站验证；不修改任一候选源码，不运行模型、训练、推理、转换、评测或 Ascend 910B smoke。
- 公开仓库永不追踪源码树、模型权重、数据集、checkpoint、Git LFS object、密钥、令牌或受限媒体；只追踪 acquisition metadata、文件/符号/配置索引、必要短引用、固定链接和生成 HTML。
- 四个本地输入一律只读：Qwen3-TTS `022e286b...` 与 MOSS-TTS `ad99ec5f...` 是 sparse Git checkout；MindSpeed-MM `0edd553e...` 与 MindSpeed-LLM `434baff7...` 是 codeload archive snapshot，绝不称为 clone 或 checkout。
- 索引 CLI 必须显式接收 `--source-root`、`--snapshot-id`、`--revision`、`--output`；不得读取或要求 `.git`，不得写入输入树，输出必须对相同物化目录逐字节确定。
- 本阶段不使用 GitNexus：它要求 Git repository，并会写 `.gitnexus`/context 文件；两个入选快照是 archive，四个输入又都必须只读。以后若确有图谱价值，只能在一次性、可删除、真实 Git index workspace 中另行评估。
- 测试只读取 `tests/fixtures/source-index/` 小型 fixture，不读取 ignored source checkouts；真实四树 generation 是独立、可跳过的本地命令，机器没有 checkout 时不阻断 fixture 单元测试。
- 追踪的 index 不得含绝对本地路径、`source_root`、源码正文或无限长 quote；每个输出记录 snapshot id、完整 revision、content identity、每文件 SHA-256 和全索引 digest。
- 站点继续使用现有暖纸张三栏 shell、侧栏状态机、抽屉、复制与视觉令牌，不重新设计；所有运行时 CSS/JavaScript/搜索数据都在本地，关键正文在初始 HTML 中，禁用 JavaScript 仍可阅读。
- 学习起点是 PyTorch 单卡；本阶段只解释官方 target 静态源码，不声称一次 CUDA 或 NPU 训练已运行。
- 环境始终保留两条 lane：项目原生学习 lane 为 PyTorch/torch-npu `2.7.1` + CANN `8.5.0`；用户目标验证 lane 为 PyTorch/torch-npu `2.7.1` + CANN `8.5.2`，兼容性状态必须写 `unknown / 待真机验证`。
- 重要结论必须标注 `verified`（已证实）、`project_claim`（项目声明）、`inference`（分析推断）或 `pending_hardware`（待真机验证）；颜色不是唯一信号。
- 页面数由覆盖驱动。本计划生成 13 页，因为目标源码、训练链、两个 tokenizer、索引与搜索需要独立审阅；不得为了固定页数合并为一篇超长 HTML。
- 明确延期到后续独立计划：MindSpeed-MM 完整走读、MindSpeed-LLM scale-satellite 走读、MOSS speech/codec 对照走读、NVIDIA→Ascend migration mapping、单机 8 卡/多机实验和真实 NPU 执行。本阶段索引与固定链接必须为这些消费者保留稳定接口。
- 每个任务只提交自己的文件，提交前运行列出的验证；本计划的实施步骤不包含 push。

---

## File Map

| Path | Responsibility |
| --- | --- |
| `research/source-snapshots.json` | 四个实际 acquisition 的稳定 identity、revision、content id、物化文件数、固定链接模板与排除边界 |
| `research/schemas/source-index.schema.json` | 追踪 source index 的允许字段、类型和禁止正文约束 |
| `research/indexes/qwen3-tts-022e286b.json` | 官方 target 的文件、Python 符号和配置键索引 |
| `research/indexes/mindspeed-mm-0edd553e.json` | 主参考 archive 的文件、符号和配置键索引，供后续完整走读使用 |
| `research/indexes/mindspeed-llm-434baff7.json` | scale satellite archive 的文件、符号和配置键索引，供后续 scale plan 使用 |
| `research/indexes/moss-tts-ad99ec5f.json` | speech/codec sparse snapshot 的文件、符号和配置键索引，记录 restricted exclusion 边界 |
| `research/target-evidence.json` | target 页面使用的固定 path/line、四态证据、短引用与 claim records |
| `research/target-coverage.csv` | target index 中每个物化文件的 mapped/excluded/pending 去向和页面 section，禁止静默遗漏 |
| `content/site-foundation.json` | 首页、两个 source index 页与 search 页的顺序、正文 block 和共享导航 |
| `content/target-architecture.json` | package/API、模型、12Hz、25Hz、processor 五个 target 架构页面 |
| `content/target-training.json` | data/collate、training loop、optimizer/export、coverage/gaps 四个 target 训练页面 |
| `scripts/source_index.py` | stdlib-only discover/hash/AST/config extraction 和 canonical JSON library |
| `scripts/build_source_index.py` | 只读索引 CLI，提供四个必需参数并原子写 output |
| `scripts/phase2_contracts.py` | snapshot/index/evidence/coverage/site 验证库和稳定错误格式 |
| `scripts/validate_phase2.py` | 一次执行所有 Phase 2 contract、coverage、link、offline 和 tracked-content gate 的 CLI |
| `scripts/site_builder.py` | HTML escaping、共享 header/nav/evidence/page partial、search document 和 index table renderer |
| `scripts/build_site.py` | 从 content/evidence/index 输入生成 13 页与 `site/assets/search-index.json` 的 CLI |
| `tests/fixtures/source-index/source/README.md` | fixture 文档文件，用于路径/hash 索引 |
| `tests/fixtures/source-index/source/pkg/sample.py` | fixture class/function/method/config assignments，用于 AST 索引 |
| `tests/fixtures/source-index/source/config/sample.json` | fixture JSON key-path 配置索引 |
| `tests/fixtures/source-index/source/config/sample.toml` | fixture TOML key-path 配置索引 |
| `tests/fixtures/source-index/source/config/sample.yaml` | fixture YAML structural-key 配置索引 |
| `tests/test_source_index.py` | CLI、determinism、archive-without-Git、schema 和 forbidden-field tests |
| `tests/test_phase2_contracts.py` | snapshot identity、evidence type、coverage completeness、actual count 和 no-absolute-path gates |
| `tests/test_site_builder.py` | 13 页生成、escaping、shared partial、search index、fixed links 和 stale-output tests |
| `site/index.html` | 生成的学习路径、公开范围、双环境 lane 和 target 导航首页 |
| `site/target/package-inference-api.html` | package exports、`from_pretrained` 和三类生成 API |
| `site/target/model-architecture.html` | composite config、Talker、code predictor、speaker encoder 与 call flow |
| `site/target/tokenizer-12hz.html` | 12Hz encoder、16-codebook split/RVQ、causal/chunked decode |
| `site/target/tokenizer-25hz.html` | 25Hz encoder、DiT、BigVGAN 和公开资产/执行边界 |
| `site/target/processor-contracts.html` | processor、ChatML、text/audio 输入、采样率和 shape contracts |
| `site/target/sft-data-collate.html` | `finetuning/README.md`、`prepare_data.py`、`dataset.py` 与 dual-track collate |
| `site/target/sft-training-loop.html` | `sft_12hz.py` forward、两段 loss、backward 与 step 调用链 |
| `site/target/optimizer-checkpoint-export.html` | AdamW、Accelerate、clip、epoch save、config mutation 和 speaker row 3000 |
| `site/target/coverage-gaps.html` | target-vs-reference 覆盖、缺口、延期范围和未来硬件 validation |
| `site/indexes/source-files.html` | 四快照 source-file index 与 snapshot/acquisition filters |
| `site/indexes/symbols-configs.html` | symbol/config index，向后续主参考和卫星走读暴露固定 link interface |
| `site/search.html` | 纯本地全文检索入口和无脚本 alphabetic fallback |
| `site/assets/search-index.json` | 生成的 page/file/symbol/config 搜索文档；运行时同时内嵌于 `search.html` |
| `site/assets/app.js` | 保留侧栏/抽屉/复制逻辑，增加 inline local search controller |
| `site/assets/theme.css` | 保留视觉令牌，增加 status/table/contract/search-result styles |
| `site/assets/layout.css` | 保留断点/打印，增加生成页 table/search reflow 规则 |
| `tests/site/template-structure.spec.js` | 将模板断言泛化为所有生成页共享 shell contract |
| `tests/site/final-review-regressions.spec.js` | 将旧示例固定 source assertion 更新为 Qwen target immutable link |
| `tests/site/template-visual.spec.js` | 继续对生成后的首页执行三视口视觉回归 |
| `tests/site/template-visual.spec.js-snapshots/*.png` | 更新后的首页 desktop/laptop/mobile 基线 |
| `tests/site/phase2-navigation-search.spec.js` | 多页相邻导航、文件/符号 index、local search 与 offline link regression |
| `tests/site/phase2-responsive-accessibility.spec.js` | 代表性长页在 1440/1024/390、200% reflow、无脚本和 axe 的回归 |

### Task 1: 固化四快照 identity 与 source-index schema

**Files:**
- Create: `research/source-snapshots.json`
- Create: `research/schemas/source-index.schema.json`
- Create: `scripts/phase2_contracts.py`
- Create: `tests/test_phase2_contracts.py`

**Interfaces:**
- Consumes: four acquisition handoffs and the actual read-only trees verified in Task 7.
- Produces: `load_snapshot_registry(path: Path) -> dict[str, Snapshot]`, `validate_snapshot_registry(data: object) -> list[str]`, `validate_source_index(data: object, registry: dict[str, Snapshot]) -> list[str]`; immutable `Snapshot(snapshot_id, project, role, revision, acquisition_kind, content_id, materialized_file_count, blob_url_template)`.

- [ ] **Step 1: 写入失败的 registry contract tests**

Create `tests/test_phase2_contracts.py` with these initial tests:

```python
import json
import unittest
from pathlib import Path

from scripts.phase2_contracts import load_snapshot_registry, validate_snapshot_registry

ROOT = Path(__file__).resolve().parents[1]


class SnapshotRegistryTest(unittest.TestCase):
    def test_registry_preserves_real_acquisition_kinds_and_counts(self):
        snapshots = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        self.assertEqual(snapshots["qwen3-tts-022e286b"].acquisition_kind, "git-sparse-checkout")
        self.assertEqual(snapshots["mindspeed-mm-0edd553e"].acquisition_kind, "codeload-archive")
        self.assertEqual(snapshots["mindspeed-llm-434baff7"].acquisition_kind, "codeload-archive")
        self.assertEqual(snapshots["moss-tts-ad99ec5f"].acquisition_kind, "git-sparse-checkout")
        self.assertEqual(sum(item.materialized_file_count for item in snapshots.values()), 3270)

    def test_registry_rejects_local_paths_and_git_claim_for_archives(self):
        data = json.loads((ROOT / "research/source-snapshots.json").read_text())
        data["snapshots"][1]["local_path"] = "/Users/example/archive"
        data["snapshots"][1]["acquisition_kind"] = "git-clone"
        errors = validate_snapshot_registry(data)
        self.assertIn("snapshots[1]: unknown field local_path", errors)
        self.assertIn("snapshots[1].acquisition_kind: expected codeload-archive", errors)
```

- [ ] **Step 2: 运行 tests 并确认缺少 contract module**

Run: `python3 -m unittest tests.test_phase2_contracts -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.phase2_contracts'`.

- [ ] **Step 3: 写入真实 snapshot registry**

Create `research/source-snapshots.json` exactly with schema version `1` and these four records (no local path field):

```json
{
  "schema_version": 1,
  "snapshots": [
    {
      "snapshot_id": "qwen3-tts-022e286b",
      "project": "QwenLM/Qwen3-TTS",
      "role": "official-target",
      "revision": "022e286b98fbec7e1e916cb940cdf532cd9f488e",
      "acquisition_kind": "git-sparse-checkout",
      "content_id": "git-tree:33e4644dc5a698874fa035630d1878aa453b564c",
      "materialized_file_count": 35,
      "source_url": "https://github.com/QwenLM/Qwen3-TTS",
      "blob_url_template": "https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/{path}#L{start}-L{end}",
      "excluded": {"count": 2, "reason": "sparse source-only checkout excludes rendered paper and macOS metadata"}
    },
    {
      "snapshot_id": "mindspeed-mm-0edd553e",
      "project": "Ascend/MindSpeed-MM",
      "role": "main-reference",
      "revision": "0edd553e0ac9c912fe422c42cc9f42db9255ddcf",
      "acquisition_kind": "codeload-archive",
      "content_id": "archive-sha256:1b52f9a6a8e3536f02a7a06ed01cc4d00dafc57617783ca2a04d0250b670ba15",
      "materialized_file_count": 1405,
      "source_url": "https://gitcode.com/Ascend/MindSpeed-MM",
      "blob_url_template": "https://github.com/Ascend/MindSpeed-MM/blob/0edd553e0ac9c912fe422c42cc9f42db9255ddcf/{path}#L{start}-L{end}",
      "excluded": {"count": 0, "reason": "exact-SHA codeload tree; no Git metadata retained"}
    },
    {
      "snapshot_id": "mindspeed-llm-434baff7",
      "project": "Ascend/MindSpeed-LLM",
      "role": "scale-satellite",
      "revision": "434baff794bd5594ebc9ed8a5b399110da9a44f0",
      "acquisition_kind": "codeload-archive",
      "content_id": "git-tree:a00c5d3bc01d3357a9c943fef923571b5df676e2",
      "materialized_file_count": 1664,
      "source_url": "https://gitcode.com/Ascend/MindSpeed-LLM",
      "blob_url_template": "https://github.com/Ascend/MindSpeed-LLM/blob/434baff794bd5594ebc9ed8a5b399110da9a44f0/{path}#L{start}-L{end}",
      "excluded": {"count": 0, "reason": "tree-hash-verified exact-SHA codeload tree; no Git metadata retained"}
    },
    {
      "snapshot_id": "moss-tts-ad99ec5f",
      "project": "OpenMOSS/MOSS-TTS",
      "role": "speech-codec-satellite",
      "revision": "ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af",
      "acquisition_kind": "git-sparse-checkout",
      "content_id": "git-tree:a85bd2dd897f643413c4f3df2f32c3f59f6d8c37",
      "materialized_file_count": 166,
      "source_url": "https://github.com/OpenMOSS/MOSS-TTS",
      "blob_url_template": "https://github.com/OpenMOSS/MOSS-TTS/blob/ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af/{path}#L{start}-L{end}",
      "excluded": {"count": 18, "reason": "source-only sparse checkout excludes committed wav/mp3/m4a/jsonl assets; tokenizer submodule remains uninitialized"}
    }
  ]
}
```

- [ ] **Step 4: 写入允许字段严格的 JSON schema**

Create `research/schemas/source-index.schema.json` with `additionalProperties: false` at root, snapshot, file, symbol and config levels. The root required fields are `schema_version`, `snapshot`, `indexer_version`, `files`, `symbols`, `configs`, `content_digest`; file fields are `path`, `bytes`, `sha256`, `kind`; symbol fields are `id`, `path`, `qualname`, `name`, `kind`, `line`, `end_line`; config fields are `id`, `path`, `key`, `owner`, `kind`, `line`. Do not define `source_root`, `body`, `source`, `text`, or `generated_at`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://c8x1.github.io/schemas/source-index-v1.json",
  "title": "Qwen3-TTS Ascend source index v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "snapshot", "indexer_version", "files", "symbols", "configs", "content_digest"],
  "properties": {
    "schema_version": {"const": 1},
    "snapshot": {"type": "object", "additionalProperties": false, "required": ["snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id"], "properties": {
      "snapshot_id": {"type": "string"}, "project": {"type": "string"}, "role": {"type": "string"},
      "revision": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
      "acquisition_kind": {"enum": ["git-sparse-checkout", "codeload-archive"]}, "content_id": {"type": "string"}
    }},
    "indexer_version": {"const": "1.0"},
    "files": {"type": "array", "items": {"type": "object", "additionalProperties": false, "required": ["path", "bytes", "sha256", "kind"], "properties": {
      "path": {"type": "string"}, "bytes": {"type": "integer", "minimum": 0}, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "kind": {"enum": ["python", "json", "toml", "yaml", "text", "binary"]}
    }}},
    "symbols": {"type": "array", "items": {"type": "object", "additionalProperties": false, "required": ["id", "path", "qualname", "name", "kind", "line", "end_line"], "properties": {
      "id": {"type": "string"}, "path": {"type": "string"}, "qualname": {"type": "string"}, "name": {"type": "string"}, "kind": {"enum": ["class", "function", "async_function", "method", "async_method"]}, "line": {"type": "integer", "minimum": 1}, "end_line": {"type": "integer", "minimum": 1}
    }}},
    "configs": {"type": "array", "items": {"type": "object", "additionalProperties": false, "required": ["id", "path", "key", "owner", "kind", "line"], "properties": {
      "id": {"type": "string"}, "path": {"type": "string"}, "key": {"type": "string"}, "owner": {"type": "string"}, "kind": {"enum": ["python-assignment", "json-key", "toml-key", "yaml-key"]}, "line": {"type": "integer", "minimum": 1}
    }}},
    "content_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
  }
}
```

- [ ] **Step 5: 实现 registry/index contract validation**

Create `scripts/phase2_contracts.py` with the exact public types and checks below; use a recursive allowed-key map for the complete schema and reject any absolute POSIX/Windows path in every emitted string.

```python
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ACQUISITION = {
    "qwen3-tts-022e286b": "git-sparse-checkout",
    "mindspeed-mm-0edd553e": "codeload-archive",
    "mindspeed-llm-434baff7": "codeload-archive",
    "moss-tts-ad99ec5f": "git-sparse-checkout",
}
ROOT_KEYS = {"schema_version", "snapshot", "indexer_version", "files", "symbols", "configs", "content_digest"}
FORBIDDEN_KEYS = {"source_root", "body", "source", "text", "generated_at", "local_path"}


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    project: str
    role: str
    revision: str
    acquisition_kind: str
    content_id: str
    materialized_file_count: int
    blob_url_template: str


def validate_snapshot_registry(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["registry.schema_version: expected 1"]
    for index, item in enumerate(data.get("snapshots", [])):
        for key in item:
            if key not in {"snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id", "materialized_file_count", "source_url", "blob_url_template", "excluded"}:
                errors.append(f"snapshots[{index}]: unknown field {key}")
        expected = ACQUISITION.get(item.get("snapshot_id"))
        if expected and item.get("acquisition_kind") != expected:
            errors.append(f"snapshots[{index}].acquisition_kind: expected {expected}")
        if not re.fullmatch(r"[0-9a-f]{40}", str(item.get("revision", ""))):
            errors.append(f"snapshots[{index}].revision: expected 40 lowercase hex")
    return errors


def load_snapshot_registry(path: Path) -> dict[str, Snapshot]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_snapshot_registry(data)
    if errors:
        raise ValueError("\n".join(errors))
    return {item["snapshot_id"]: Snapshot(**{key: item[key] for key in Snapshot.__dataclass_fields__}) for item in data["snapshots"]}


def validate_source_index(data: object, registry: dict[str, Snapshot]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["index: expected object"]
    for key in data:
        if key not in ROOT_KEYS:
            errors.append(f"index: unknown field {key}")
    if FORBIDDEN_KEYS.intersection(data):
        errors.append("index: forbidden source-body or local-path field")
    snapshot_id = data.get("snapshot", {}).get("snapshot_id")
    if snapshot_id not in registry:
        errors.append(f"snapshot.snapshot_id: unknown {snapshot_id}")
    for row_name in ("files", "symbols", "configs"):
        rows = data.get(row_name, [])
        if rows != sorted(rows, key=lambda row: row["id"] if "id" in row else row["path"]):
            errors.append(f"{row_name}: not deterministically sorted")
        for row in rows:
            for key, value in row.items():
                if key in FORBIDDEN_KEYS:
                    errors.append(f"{row_name}.{key}: forbidden")
                if isinstance(value, str) and (value.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", value)):
                    errors.append(f"{row_name}.{key}: absolute path forbidden")
    return errors
```

- [ ] **Step 6: 运行 contract tests**

Run: `python3 -m unittest tests.test_phase2_contracts -v`

Expected: 2 tests pass.

- [ ] **Step 7: 提交 snapshot contract**

```bash
git add research/source-snapshots.json research/schemas/source-index.schema.json scripts/phase2_contracts.py tests/test_phase2_contracts.py
git commit -m "feat: define source snapshot index contracts"
```

Expected: one commit; `git status --short` has no output.

### Task 2: 实现 deterministic stdlib-only source indexer

**Files:**
- Create: `tests/fixtures/source-index/source/README.md`
- Create: `tests/fixtures/source-index/source/pkg/sample.py`
- Create: `tests/fixtures/source-index/source/config/sample.json`
- Create: `tests/fixtures/source-index/source/config/sample.toml`
- Create: `tests/fixtures/source-index/source/config/sample.yaml`
- Create: `tests/test_source_index.py`
- Create: `scripts/source_index.py`
- Create: `scripts/build_source_index.py`

**Interfaces:**
- Consumes: `Snapshot` registry records and any readable directory, including directories without `.git`.
- Produces: `build_index(source_root: Path, snapshot: Snapshot) -> dict[str, object]`, `write_canonical_json(data: object, output: Path) -> None`, and CLI `python3 scripts/build_source_index.py --source-root PATH --snapshot-id ID --revision SHA --output FILE`.

- [ ] **Step 1: 建立不依赖 ignored trees 的 fixture**

Create the five fixture files with deterministic content:

```python
# tests/fixtures/source-index/source/pkg/sample.py
DEFAULT_RATE = 24000


class SampleConfig:
    model_type = "sample"

    def __init__(self, width=16):
        self.width = width

    def describe(self):
        return self.width


def build(config: SampleConfig):
    return config.describe()
```

```json
{"model": {"name": "fixture", "layers": 2}, "training": {"precision": "bf16"}}
```

```toml
[model]
name = "fixture"
[training]
precision = "bf16"
```

```yaml
model:
  name: fixture
training:
  precision: bf16
```

`README.md` contains exactly `# Source-index fixture\n`.

- [ ] **Step 2: 写入 CLI、determinism 和 no-Git failing tests**

Create `tests/test_source_index.py`:

```python
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.phase2_contracts import Snapshot, validate_source_index
from scripts.source_index import build_index, file_kind, write_canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/source-index/source"
SNAPSHOT = Snapshot("fixture", "Fixture/Source", "test", "a" * 40, "codeload-archive", "fixture:1", 5, "https://example.invalid/{path}#L{start}-L{end}")


class SourceIndexTest(unittest.TestCase):
    def test_builds_files_symbols_and_config_keys_without_git(self):
        data = build_index(FIXTURE, SNAPSHOT)
        self.assertEqual(len(data["files"]), 5)
        self.assertEqual([row["qualname"] for row in data["symbols"]], ["SampleConfig", "SampleConfig.__init__", "SampleConfig.describe", "build"])
        keys = {row["key"] for row in data["configs"]}
        self.assertTrue({"DEFAULT_RATE", "SampleConfig.model_type", "SampleConfig.width", "model.name", "training.precision"}.issubset(keys))
        self.assertEqual(validate_source_index(data, {"fixture": SNAPSHOT}), [])

    def test_same_tree_produces_identical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "one.json", Path(tmp) / "two.json"
            data = build_index(FIXTURE, SNAPSHOT)
            write_canonical_json(data, first)
            write_canonical_json(build_index(FIXTURE, SNAPSHOT), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_cli_requires_explicit_revision_and_rejects_mismatch(self):
        result = subprocess.run([
            "python3", "scripts/build_source_index.py", "--source-root", str(FIXTURE),
            "--snapshot-id", "qwen3-tts-022e286b", "--revision", "0" * 40,
            "--output", "/tmp/should-not-exist.json",
        ], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("revision does not match registry", result.stderr)

    def test_rejects_symlinks_before_hashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "safe.py").write_text("VALUE = 1\n")
            (source / "escape.py").symlink_to(FIXTURE / "pkg/sample.py")
            with self.assertRaisesRegex(ValueError, "symlink forbidden: escape.py"):
                build_index(source, SNAPSHOT)

    def test_extensionless_and_packaging_files_are_text_metadata(self):
        names = ["LICENSE", "Makefile", "Dockerfile", "MANIFEST.in", ".gitignore", "README"]
        self.assertEqual([file_kind(Path(name)) for name in names], ["text"] * len(names))
```

- [ ] **Step 3: 运行 tests 并确认 index library 缺失**

Run: `python3 -m unittest tests.test_source_index -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.source_index'`.

- [ ] **Step 4: 实现文件发现、hash、AST 和 config-key extraction**

Create `scripts/source_index.py`. It must never call Git, must prune only `.git`, `__pycache__`, `.pytest_cache`, `node_modules`, `playwright-report`, and `test-results`, and must index every other regular file as path/size/hash metadata. Python parsing emits classes, top-level functions and methods; config extraction emits names only, never scalar values.

```python
from __future__ import annotations

import ast
import hashlib
import json
import re
import tomllib
from pathlib import Path

from scripts.phase2_contracts import Snapshot

PRUNED = {".git", "__pycache__", ".pytest_cache", "node_modules", "playwright-report", "test-results"}
KINDS = {".py": "python", ".json": "json", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml"}
TEXT_SUFFIXES = {".md", ".rst", ".txt", ".sh", ".css", ".js", ".html", ".c", ".h", ".in"}
TEXT_NAMES = {"LICENSE", "Makefile", "Dockerfile", "README", ".gitignore", ".gitattributes", ".gitmodules"}


def discover_files(source_root: Path) -> list[Path]:
    if not source_root.is_dir():
        raise ValueError(f"source root is not a directory: {source_root}")
    files = []
    for path in source_root.rglob("*"):
        relative = path.relative_to(source_root)
        if PRUNED.intersection(relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {relative.as_posix()}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(source_root).as_posix())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_kind(path: Path) -> str:
    if path.suffix.lower() in KINDS:
        return KINDS[path.suffix.lower()]
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
        return "text"
    return "binary"


def symbol_rows(path: Path, relative: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    rows = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            rows.append(_symbol(relative, node.name, node.name, "class", node))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = "async_method" if isinstance(child, ast.AsyncFunctionDef) else "method"
                    rows.append(_symbol(relative, f"{node.name}.{child.name}", child.name, kind, child))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            rows.append(_symbol(relative, node.name, node.name, kind, node))
    return rows


def _symbol(path: str, qualname: str, name: str, kind: str, node: ast.AST) -> dict[str, object]:
    return {"id": f"{path}:{qualname}", "path": path, "qualname": qualname, "name": name, "kind": kind, "line": node.lineno, "end_line": node.end_lineno}


def config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return python_config_rows(path, relative)
    if suffix == ".json":
        return nested_config_rows(json.loads(path.read_text(encoding="utf-8")), relative, "json-key")
    if suffix == ".toml":
        return nested_config_rows(tomllib.loads(path.read_text(encoding="utf-8")), relative, "toml-key")
    if suffix in {".yaml", ".yml"}:
        return yaml_config_rows(path, relative)
    return []


def python_config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    visitor = ConfigVisitor(relative)
    visitor.visit(tree)
    return visitor.rows


class ConfigVisitor(ast.NodeVisitor):
    def __init__(self, relative: str):
        self.relative = relative
        self.owners: list[str] = []
        self.rows: list[dict[str, object]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.owners.append(node.name)
        self.generic_visit(node)
        self.owners.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        self._record(node.targets, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record([node.target], node.lineno)
        self.generic_visit(node)

    def _record(self, targets: list[ast.expr], line: int) -> None:
        owner = ".".join(self.owners)
        for target in targets:
            name = None
            if isinstance(target, ast.Name) and (target.id.isupper() or target.id in {"model_type", "sub_configs"}):
                name = target.id
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                name = target.attr
            if name is None:
                continue
            key = f"{owner}.{name}" if owner else name
            self.rows.append({"id": f"{self.relative}:{key}:{line}", "path": self.relative, "key": key, "owner": owner, "kind": "python-assignment", "line": line})


def nested_config_rows(data: object, relative: str, kind: str, prefix: str = "") -> list[dict[str, object]]:
    rows = []
    if isinstance(data, dict):
        for key in sorted(data):
            dotted = f"{prefix}.{key}" if prefix else str(key)
            rows.append({"id": f"{relative}:{dotted}", "path": relative, "key": dotted, "owner": prefix, "kind": kind, "line": 1})
            rows.extend(nested_config_rows(data[key], relative, kind, dotted))
    return rows


def yaml_config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    rows, stack = [], []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = re.match(r"^( *)([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if not match or line.lstrip().startswith("#"):
            continue
        depth = len(match.group(1))
        stack = [(indent, key) for indent, key in stack if indent < depth]
        stack.append((depth, match.group(2)))
        dotted = ".".join(key for _, key in stack)
        rows.append({"id": f"{relative}:{dotted}:{line_number}", "path": relative, "key": dotted, "owner": ".".join(key for _, key in stack[:-1]), "kind": "yaml-key", "line": line_number})
    return rows


def build_index(source_root: Path, snapshot: Snapshot) -> dict[str, object]:
    files, symbols, configs = [], [], []
    for path in discover_files(source_root):
        relative = path.relative_to(source_root).as_posix()
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path), "kind": file_kind(path)})
        symbols.extend(symbol_rows(path, relative))
        configs.extend(config_rows(path, relative))
    payload = {
        "schema_version": 1,
        "snapshot": {key: getattr(snapshot, key) for key in ("snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id")},
        "indexer_version": "1.0",
        "files": sorted(files, key=lambda row: row["path"]),
        "symbols": sorted(symbols, key=lambda row: row["id"]),
        "configs": sorted(configs, key=lambda row: row["id"]),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    payload["content_digest"] = hashlib.sha256(canonical).hexdigest()
    return payload


def write_canonical_json(data: object, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
```

- [ ] **Step 5: 实现四参数 CLI 和 identity checks**

Create `scripts/build_source_index.py`:

```python
#!/usr/bin/env python3
import argparse
from pathlib import Path

from scripts.phase2_contracts import load_snapshot_registry, validate_source_index
from scripts.source_index import build_index, write_canonical_json

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
    snapshot = registry.get(args.snapshot_id)
    if snapshot is None:
        parser.error(f"unknown snapshot id: {args.snapshot_id}")
    if args.revision != snapshot.revision:
        parser.error("revision does not match registry")
    data = build_index(args.source_root, snapshot)
    errors = validate_source_index(data, registry)
    if errors:
        parser.error("; ".join(errors))
    write_canonical_json(data, args.output)
    print(f"wrote {args.output.as_posix()} snapshot={snapshot.snapshot_id} revision={snapshot.revision} files={len(data['files'])} digest={data['content_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: 运行 fixture tests 和 command help**

Run:

```bash
python3 -m unittest tests.test_source_index -v
python3 scripts/build_source_index.py --help
```

Expected: 5 tests pass; help lists all four required flags; no `.superpowers/source-checkouts` path is opened by tests; the symlink test proves hashing cannot escape `--source-root`; extensionless packaging files are classified as text metadata.

- [ ] **Step 7: 提交 indexer**

```bash
git add scripts/source_index.py scripts/build_source_index.py tests/test_source_index.py tests/fixtures/source-index
git commit -m "feat: add deterministic source indexer"
```

Expected: one commit; `git status --short` has no output.
### Task 3: 生成并验证四个可追踪 source indexes

**Files:**
- Modify: `tests/test_phase2_contracts.py`
- Create: `scripts/validate_phase2.py`
- Create: `research/indexes/qwen3-tts-022e286b.json`
- Create: `research/indexes/mindspeed-mm-0edd553e.json`
- Create: `research/indexes/mindspeed-llm-434baff7.json`
- Create: `research/indexes/moss-tts-ad99ec5f.json`

**Interfaces:**
- Consumes: `build_source_index.py`, the four exact read-only roots, and the registry's expected file counts.
- Produces: four schema-v1 indexes totaling exactly 3,270 materialized files; CLI `python3 scripts/validate_phase2.py --indexes-only` and reproducibility proof by regenerating to a temporary directory.

- [ ] **Step 1: 扩展 index validation tests**

Append these tests to `tests/test_phase2_contracts.py`:

```python
from scripts.phase2_contracts import validate_source_index


class SourceIndexContractTest(unittest.TestCase):
    def test_index_rejects_absolute_path_and_body(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        data = {
            "schema_version": 1,
            "snapshot": {"snapshot_id": "qwen3-tts-022e286b"},
            "indexer_version": "1.0",
            "files": [{"path": "/Users/me/source.py", "bytes": 1, "sha256": "0" * 64, "kind": "python", "body": "print(1)"}],
            "symbols": [], "configs": [], "content_digest": "0" * 64,
        }
        errors = validate_source_index(data, registry)
        self.assertTrue(any("absolute path forbidden" in error for error in errors))
        self.assertTrue(any("forbidden" in error for error in errors))

    def test_tracked_indexes_match_registry_counts_and_revisions(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        for snapshot_id, snapshot in registry.items():
            data = json.loads((ROOT / "research/indexes" / f"{snapshot_id}.json").read_text())
            self.assertEqual(data["snapshot"]["revision"], snapshot.revision)
            self.assertEqual(len(data["files"]), snapshot.materialized_file_count)
            self.assertEqual(validate_source_index(data, registry), [])
```

- [ ] **Step 2: 运行 contract tests 并确认 indexes 缺失**

Run: `python3 -m unittest tests.test_phase2_contracts.SourceIndexContractTest -v`

Expected: the forbidden-field test passes and the tracked-index test fails with `FileNotFoundError` for `research/indexes/qwen3-tts-022e286b.json`.

- [ ] **Step 3: 对四棵实际树运行显式 generation commands**

Run exactly:

```bash
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/qwen3-tts-022e286b --snapshot-id qwen3-tts-022e286b --revision 022e286b98fbec7e1e916cb940cdf532cd9f488e --output research/indexes/qwen3-tts-022e286b.json
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/mindspeed-mm-0edd553e-archive --snapshot-id mindspeed-mm-0edd553e --revision 0edd553e0ac9c912fe422c42cc9f42db9255ddcf --output research/indexes/mindspeed-mm-0edd553e.json
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/mindspeed-llm-434baff7-archive --snapshot-id mindspeed-llm-434baff7 --revision 434baff794bd5594ebc9ed8a5b399110da9a44f0 --output research/indexes/mindspeed-llm-434baff7.json
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/moss-tts-ad99ec5f --snapshot-id moss-tts-ad99ec5f --revision ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af --output research/indexes/moss-tts-ad99ec5f.json
```

Expected: each command exits 0; stdout reports respectively `files=35`, `files=1405`, `files=1664`, and `files=166`; every digest is 64 lowercase hexadecimal characters. The archive commands succeed without a `.git` directory and no input-tree mtime or status changes.

- [ ] **Step 4: 实现 Phase 2 index validation CLI**

Create `scripts/validate_phase2.py` with an `--indexes-only` mode. It must recompute `content_digest` after removing the digest field, verify exact counts, unique paths/IDs, path sorting, revision/content identity, and schema checks; it exits nonzero with one error per line.

```python
#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

from scripts.phase2_contracts import load_snapshot_registry, validate_source_index

ROOT = Path(__file__).resolve().parents[1]


def validate_indexes() -> list[str]:
    errors = []
    registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
    for snapshot_id, snapshot in registry.items():
        path = ROOT / "research/indexes" / f"{snapshot_id}.json"
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: missing")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(f"{path.name}: {error}" for error in validate_source_index(data, registry))
        if data["snapshot"] != {key: getattr(snapshot, key) for key in ("snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id")}:
            errors.append(f"{path.name}: snapshot metadata mismatch")
        if len(data["files"]) != snapshot.materialized_file_count:
            errors.append(f"{path.name}: expected {snapshot.materialized_file_count} files")
        payload = dict(data)
        actual = payload.pop("content_digest")
        expected = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if actual != expected:
            errors.append(f"{path.name}: content digest mismatch")
        for key in ("files", "symbols", "configs"):
            identity = "path" if key == "files" else "id"
            values = [row[identity] for row in data[key]]
            if len(values) != len(set(values)):
                errors.append(f"{path.name}: duplicate {key} {identity}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indexes-only", action="store_true")
    args = parser.parse_args()
    errors = validate_indexes()
    if errors:
        print("\n".join(errors))
        return 1
    print("validated 4 source indexes: 3270 files; no absolute paths or source bodies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 验证 indexes 并做逐字节 reproduction**

Run:

```bash
python3 scripts/validate_phase2.py --indexes-only
tmpdir="$(mktemp -d)"
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/qwen3-tts-022e286b --snapshot-id qwen3-tts-022e286b --revision 022e286b98fbec7e1e916cb940cdf532cd9f488e --output "$tmpdir/qwen3-tts-022e286b.json"
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/mindspeed-mm-0edd553e-archive --snapshot-id mindspeed-mm-0edd553e --revision 0edd553e0ac9c912fe422c42cc9f42db9255ddcf --output "$tmpdir/mindspeed-mm-0edd553e.json"
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/mindspeed-llm-434baff7-archive --snapshot-id mindspeed-llm-434baff7 --revision 434baff794bd5594ebc9ed8a5b399110da9a44f0 --output "$tmpdir/mindspeed-llm-434baff7.json"
python3 scripts/build_source_index.py --source-root .superpowers/source-checkouts/moss-tts-ad99ec5f --snapshot-id moss-tts-ad99ec5f --revision ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af --output "$tmpdir/moss-tts-ad99ec5f.json"
cmp research/indexes/qwen3-tts-022e286b.json "$tmpdir/qwen3-tts-022e286b.json"
cmp research/indexes/mindspeed-mm-0edd553e.json "$tmpdir/mindspeed-mm-0edd553e.json"
cmp research/indexes/mindspeed-llm-434baff7.json "$tmpdir/mindspeed-llm-434baff7.json"
cmp research/indexes/moss-tts-ad99ec5f.json "$tmpdir/moss-tts-ad99ec5f.json"
rm -rf "$tmpdir"
```

Expected: validator prints exactly `validated 4 source indexes: 3270 files; no absolute paths or source bodies`; all four `cmp` commands are silent and exit 0. On a machine without checkouts, skip only this reproduction block; fixture tests and validation of already committed outputs still run.

- [ ] **Step 6: 审计公开追踪边界**

Run:

```bash
git ls-files | rg '(^|/)\.superpowers/source-checkouts/|\.(safetensors|ckpt|pt|pth|onnx|gguf|wav|mp3|m4a|flac)$|(^|/)(weights|datasets|checkpoints)(/|$)' && exit 1 || true
rg -n '"(source_root|body|source|text|local_path)"\s*:' research/indexes
rg -n '/Users/|[A-Za-z]:\\\\' research/indexes
```

Expected: all three audits have no output; no source tree, asset, full source body, or absolute local path is tracked.

- [ ] **Step 7: 运行 Python suite 并提交 indexes**

Run: `python3 -m unittest discover -s tests -p 'test_*.py' -v`

Expected: the existing 15 research tests plus 9 Phase 2/index tests pass (24 total).

```bash
git add scripts/validate_phase2.py tests/test_phase2_contracts.py research/indexes
git commit -m "data: add reproducible selected source indexes"
```

Expected: one commit containing only validator/test/index outputs; no ignored tree is staged.

### Task 4: 建立 target evidence 与 no-silent-omission coverage contracts

**Files:**
- Create: `research/target-evidence.json`
- Create: `research/target-coverage.csv`
- Modify: `tests/test_phase2_contracts.py`
- Modify: `scripts/phase2_contracts.py`
- Modify: `scripts/validate_phase2.py`

**Interfaces:**
- Consumes: target source index `qwen3-tts-022e286b.json`, fixed target blob URL template, official baseline and approved selection proposal.
- Produces: `load_evidence(path: Path) -> dict[str, Evidence]`, `validate_evidence(data: object, registry) -> list[str]`, `validate_target_coverage(index, rows, page_catalog=None) -> list[str]`; exactly one coverage row for each of 35 materialized target files.

- [ ] **Step 1: 写入 evidence/coverage failing tests**

Append:

```python
from scripts.phase2_contracts import load_evidence, validate_target_coverage


class TargetCoverageTest(unittest.TestCase):
    def test_every_target_file_has_exactly_one_disposition(self):
        target = json.loads((ROOT / "research/indexes/qwen3-tts-022e286b.json").read_text())
        errors = validate_target_coverage(target, ROOT / "research/target-coverage.csv")
        self.assertEqual(errors, [])

    def test_evidence_has_four_states_and_bounded_quotes(self):
        evidence = load_evidence(ROOT / "research/target-evidence.json")
        self.assertEqual({row.state for row in evidence.values()}, {"verified", "project_claim", "inference", "pending_hardware"})
        self.assertTrue(all(len(row.quote) <= 240 and row.quote.count("\n") < 8 for row in evidence.values()))
```

- [ ] **Step 2: 运行 tests 并确认 evidence/coverage 缺失**

Run: `python3 -m unittest tests.test_phase2_contracts.TargetCoverageTest -v`

Expected: FAIL with `FileNotFoundError` for `research/target-coverage.csv` or `research/target-evidence.json`.

- [ ] **Step 3: 写入 fixed target evidence records**

Create `research/target-evidence.json` with `schema_version: 1`. Every record has `evidence_id`, `snapshot_id`, `path`, `start_line`, `end_line`, `state`, `claim`, and `quote`; `quote` may be empty but never exceeds 240 characters. Use exactly these grounded records:

| Evidence ID | Path and fixed lines | State | Claim used by pages |
| --- | --- | --- | --- |
| `TGT-SCOPE-001` | `finetuning/README.md:3-10` | `verified` | public recipe is 12Hz Base single-speaker SFT; advanced/multi-speaker work is not public here |
| `TGT-SCOPE-002` | `README.md:1-220` | `project_claim` | released family, quality and latency statements remain project claims |
| `TGT-PKG-001` | `pyproject.toml:1-45` | `verified` | package metadata, Python floor and runtime dependencies |
| `TGT-API-001` | `qwen_tts/inference/qwen3_tts_model.py:83-121` | `verified` | `from_pretrained` registers AutoConfig/AutoModel/AutoProcessor then loads model and processor |
| `TGT-API-002` | `qwen_tts/inference/qwen3_tts_model.py:356-633` | `verified` | Base voice clone prompt and generation API |
| `TGT-API-003` | `qwen_tts/inference/qwen3_tts_model.py:637-839` | `verified` | VoiceDesign and CustomVoice public wrapper APIs |
| `TGT-CONFIG-001` | `qwen_tts/core/models/configuration_qwen3_tts.py:22-499` | `verified` | speaker, code predictor, Talker and composite config nesting |
| `TGT-MODEL-001` | `qwen_tts/core/models/modeling_qwen3_tts.py:311-393` | `verified` | ECAPA-style speaker encoder produces the speaker embedding |
| `TGT-MODEL-002` | `qwen_tts/core/models/modeling_qwen3_tts.py:1427-1810` | `verified` | Talker backbone, codec-0 LM head and residual code predictor integration |
| `TGT-MODEL-003` | `qwen_tts/core/models/modeling_qwen3_tts.py:1813-2292` | `verified` | composite conditional generation and prompt/speaker injection flow |
| `TGT-MODEL-004` | `qwen_tts/core/models/modeling_qwen3_tts.py:1612-1633` | `verified` | `forward_sub_talker_finetune` returns residual-codebook loss |
| `TGT-TOK12-001` | `qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py:780-1024` | `verified` | split RVQ, 12Hz model encode/decode and causal/chunked decoder |
| `TGT-TOK25-001` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:996-1526` | `verified` | 25Hz encoder, DiT mel decoder and BigVGAN waveform decoder source exists |
| `TGT-TOK25-002` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:1397-1442` | `pending_hardware` | external 25Hz runtime assets are required and public executable coverage remains unknown |
| `TGT-PROC-001` | `qwen_tts/core/models/processing_qwen3_tts.py:27-103` | `verified` | processor wraps Qwen tokenizer/ChatML text behavior |
| `TGT-PROC-002` | `qwen_tts/inference/qwen3_tts_tokenizer.py:44-410` | `verified` | 12Hz/25Hz audio wrapper normalizes, encodes, decodes and exposes sample-rate contracts |
| `TGT-DATA-001` | `finetuning/prepare_data.py:24-68` | `verified` | preprocessing materializes `audio_codes` into JSONL |
| `TGT-DATA-002` | `finetuning/dataset.py:33-217` | `verified` | dataset makes ChatML text, 24kHz reference mel and dual-track collate tensors |
| `TGT-TRAIN-001` | `finetuning/sft_12hz.py:31-125` | `verified` | Accelerate BF16, AdamW, main + 0.3 residual loss, backward, clip and step |
| `TGT-EXPORT-001` | `finetuning/sft_12hz.py:126-158` | `verified` | per-epoch copy/config mutation, speaker row 3000 and safetensors export |
| `TGT-GAP-001` | `finetuning/sft_12hz.py:31-158` | `inference` | absence of scheduler/resume/validation in this file is a fixed-tree audit inference, not proof of global absence |
| `TGT-HW-001` | `pyproject.toml:1-45` | `pending_hardware` | no CANN/torch-npu dependency or CANN 8.5.2 compatibility evidence exists in the official target package |

For the four non-empty quotes use only these short excerpts: `single-speaker fine-tuning`, `AutoModel.from_pretrained`, `main_loss + 0.3 * sub_talker_loss`, and `checkpoint-epoch-{epoch}`; all other `quote` values are empty. Generate each `url` at validation/render time from the registry template rather than duplicating it in this file.

- [ ] **Step 4: 写入 35-row coverage matrix**

Create `research/target-coverage.csv` with header:

```csv
path,disposition,page,section,evidence_ids,reason
```

Use these exact dispositions; the validator requires a non-empty reason for `excluded`/`pending` and a page/section for `mapped`/`pending`:

```csv
.github/ISSUE_TEMPLATE/bug_report.yml,excluded,,,,Repository governance form; not runtime or training source
.github/ISSUE_TEMPLATE/config.yml,excluded,,,,Repository governance form; not runtime or training source
.github/workflows/inactive.yaml,excluded,,,,Repository maintenance workflow; not target execution flow
.github/workflows/translate.yaml,excluded,,,,Repository translation workflow; not target execution flow
.gitignore,excluded,,,,Repository hygiene only
LICENSE,mapped,index.html,public-scope,TGT-PKG-001,
MANIFEST.in,mapped,target/package-inference-api.html,package-layout,TGT-PKG-001,
README.md,mapped,index.html,public-scope,TGT-SCOPE-002,
examples/test_model_12hz_base.py,mapped,target/package-inference-api.html,base-api,TGT-API-002,
examples/test_model_12hz_custom_voice.py,mapped,target/package-inference-api.html,custom-api,TGT-API-003,
examples/test_model_12hz_voice_design.py,mapped,target/package-inference-api.html,voice-design-api,TGT-API-003,
examples/test_tokenizer_12hz.py,mapped,target/tokenizer-12hz.html,wrapper-example,TGT-TOK12-001,
finetuning/README.md,mapped,target/sft-data-collate.html,public-recipe,TGT-SCOPE-001,
finetuning/dataset.py,mapped,target/sft-data-collate.html,collate-contract,TGT-DATA-002,
finetuning/prepare_data.py,mapped,target/sft-data-collate.html,offline-codes,TGT-DATA-001,
finetuning/sft_12hz.py,mapped,target/sft-training-loop.html,training-loop,TGT-TRAIN-001|TGT-EXPORT-001,
pyproject.toml,mapped,target/package-inference-api.html,dependencies,TGT-PKG-001,
qwen_tts/__init__.py,mapped,target/package-inference-api.html,package-exports,TGT-API-001,
qwen_tts/__main__.py,mapped,target/package-inference-api.html,cli-entry,TGT-API-001,
qwen_tts/cli/demo.py,mapped,target/package-inference-api.html,cli-demo,TGT-API-003,
qwen_tts/core/__init__.py,excluded,,,,Empty package marker
qwen_tts/core/models/__init__.py,mapped,target/model-architecture.html,model-exports,TGT-CONFIG-001,
qwen_tts/core/models/configuration_qwen3_tts.py,mapped,target/model-architecture.html,composite-config,TGT-CONFIG-001,
qwen_tts/core/models/modeling_qwen3_tts.py,mapped,target/model-architecture.html,model-call-flow,TGT-MODEL-001|TGT-MODEL-002|TGT-MODEL-003|TGT-MODEL-004,
qwen_tts/core/models/processing_qwen3_tts.py,mapped,target/processor-contracts.html,text-contract,TGT-PROC-001,
qwen_tts/core/tokenizer_12hz/configuration_qwen3_tts_tokenizer_v2.py,mapped,target/tokenizer-12hz.html,configuration,TGT-TOK12-001,
qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py,mapped,target/tokenizer-12hz.html,encode-decode,TGT-TOK12-001,
qwen_tts/core/tokenizer_25hz/configuration_qwen3_tts_tokenizer_v1.py,pending,target/tokenizer-25hz.html,configuration,TGT-TOK25-002,25Hz public checkpoint and executable path remain unknown
qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py,pending,target/tokenizer-25hz.html,dit-bigvgan,TGT-TOK25-001|TGT-TOK25-002,Static source is mapped but runtime assets and execution are unverified
qwen_tts/core/tokenizer_25hz/vq/assets/mel_filters.npz,pending,target/tokenizer-25hz.html,bundled-filter,TGT-TOK25-002,Metadata only; binary body is never copied into the public index
qwen_tts/core/tokenizer_25hz/vq/core_vq.py,pending,target/tokenizer-25hz.html,vq-core,TGT-TOK25-001|TGT-TOK25-002,Static source is mapped but 25Hz execution remains unverified
qwen_tts/core/tokenizer_25hz/vq/speech_vq.py,pending,target/tokenizer-25hz.html,speech-vq,TGT-TOK25-001|TGT-TOK25-002,Static source is mapped but external extractor assets remain unverified
qwen_tts/core/tokenizer_25hz/vq/whisper_encoder.py,pending,target/tokenizer-25hz.html,whisper-encoder,TGT-TOK25-001|TGT-TOK25-002,Static source is mapped but external extractor assets remain unverified
qwen_tts/inference/qwen3_tts_model.py,mapped,target/package-inference-api.html,wrapper-call-flow,TGT-API-001|TGT-API-002|TGT-API-003,
qwen_tts/inference/qwen3_tts_tokenizer.py,mapped,target/processor-contracts.html,audio-wrapper,TGT-PROC-002,
```

- [ ] **Step 5: 实现 evidence and coverage validators**

Add frozen `Evidence` with the eight JSON fields plus `quote`, parse all 22 IDs uniquely, require the four-state enum, validate line order and quote bounds, and construct fixed URLs only with the snapshot registry. Implement coverage with `csv.DictReader`: compare its path multiset to target index `files`, reject unknown evidence IDs/statuses, require reasons and page/section according to disposition.

```python
@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    snapshot_id: str
    path: str
    start_line: int
    end_line: int
    state: str
    claim: str
    quote: str


EVIDENCE_STATES = {"verified", "project_claim", "inference", "pending_hardware"}
DISPOSITIONS = {"mapped", "excluded", "pending"}
```

Extend `validate_phase2.py` default mode to run `validate_indexes()`, evidence validation and coverage validation; keep `--indexes-only` behavior unchanged.

- [ ] **Step 6: 运行 contract and full validation**

Run:

```bash
python3 -m unittest tests.test_phase2_contracts -v
python3 scripts/validate_phase2.py
```

Expected: 6 Phase 2 contract tests pass; CLI prints `validated Phase 2 data: 4 indexes, 22 evidence records, 35 target coverage rows, 0 omissions`.

- [ ] **Step 7: 提交 target evidence contracts**

```bash
git add research/target-evidence.json research/target-coverage.csv scripts/phase2_contracts.py scripts/validate_phase2.py tests/test_phase2_contracts.py
git commit -m "data: map target evidence and coverage"
```

Expected: one commit; no HTML or candidate source tree is changed yet.

### Task 5: 构建共享静态页面生成器、首页、索引与本地搜索

**Files:**
- Create: `content/site-foundation.json`
- Create: `scripts/site_builder.py`
- Create: `scripts/build_site.py`
- Create: `tests/test_site_builder.py`
- Modify: `site/index.html`
- Create: `site/indexes/source-files.html`
- Create: `site/indexes/symbols-configs.html`
- Create: `site/search.html`
- Create: `site/assets/search-index.json`
- Modify: `site/assets/app.js`
- Modify: `site/assets/theme.css`
- Modify: `site/assets/layout.css`

**Interfaces:**
- Consumes: source indexes, snapshot registry, evidence records when referenced, and JSON page catalogs matching `Page(slug, title, summary, order, group, objectives, prerequisites, sections)`.
- Produces: `load_page_catalogs(paths: list[Path]) -> list[dict]`, `render_page(page, navigation, evidence, search_documents) -> str`, `build_site(output_root: Path, catalog_paths: list[Path]) -> list[Path]`; four foundation pages plus local `search-index.json` in this task.

- [ ] **Step 1: 写入生成器 failing tests**

Create `tests/test_site_builder.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts.site_builder import build_site, load_page_catalogs, script_safe_json

ROOT = Path(__file__).resolve().parents[1]


class SiteBuilderTest(unittest.TestCase):
    def test_foundation_build_is_deterministic_and_has_four_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            pages = build_site(output, [ROOT / "content/site-foundation.json"])
            first = {path.relative_to(output).as_posix(): path.read_bytes() for path in pages}
            build_site(output, [ROOT / "content/site-foundation.json"])
            second = {path.relative_to(output).as_posix(): path.read_bytes() for path in pages}
            self.assertEqual(first, second)
            self.assertEqual(set(first), {"index.html", "indexes/source-files.html", "indexes/symbols-configs.html", "search.html", "assets/search-index.json"})

    def test_generated_shell_escapes_content_and_uses_local_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "index.html").read_text()
            self.assertIn('id="chapter-nav"', html)
            self.assertIn('id="article-content"', html)
            self.assertIn('id="evidence-rail"', html)
            self.assertNotIn("https://fonts", html)
            self.assertIn('src="assets/app.js"', html)

    def test_page_catalog_has_unique_order_slug_and_section_ids(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        self.assertEqual(len({page["slug"] for page in pages}), len(pages))
        self.assertEqual(len({page["order"] for page in pages}), len(pages))
        for page in pages:
            ids = [section["id"] for section in page["sections"]]
            self.assertEqual(len(ids), len(set(ids)))

    def test_inline_search_json_cannot_close_its_script_element(self):
        encoded = script_safe_json([{"title": "</script><img src=x onerror=alert(1)>"}])
        self.assertNotIn("</script", encoded.lower())
        self.assertIn(r"\u003c/script", encoded)
```

- [ ] **Step 2: 运行 tests 并确认 builder 缺失**

Run: `python3 -m unittest tests.test_site_builder -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.site_builder'`.

- [ ] **Step 3: 写入 foundation catalog**

Create `content/site-foundation.json` with `schema_version: 1` and exactly these four pages and sections:

| Order / slug | Title | Required sections and exact teaching contract |
| --- | --- | --- |
| `1 / index.html` | `Qwen3-TTS 官方目标源码学习路径` | `public-scope`: static reading only, no training/compatibility claim; `learning-path`: PyTorch single-card → package/API → model → tokenizers → contracts → SFT; `environment-lanes`: project-native `2.7.1 + 8.5.0` and target `2.7.1 + 8.5.2 unknown`; `phase-boundary`: list all five deferred work packages |
| `11 / indexes/source-files.html` | `四个固定快照文件索引` | `snapshot-provenance`: label Git sparse vs codeload archive correctly; `file-filters`: snapshot/kind/path; `future-interface`: main/scale/speech later pages consume path+hash+fixed link |
| `12 / indexes/symbols-configs.html` | `符号与配置项索引` | `symbol-index`: qualname/kind/path/line; `config-index`: key/owner/kind/path/line with no values; `limits`: AST/static-key index is not a runtime call graph |
| `13 / search.html` | `全站搜索` | `search-results`: inline JSON-driven results; `no-script-index`: initial HTML contains alphabetic links for all pages; `search-scope`: page title/summary/headings plus file/symbol/config metadata, never full source bodies |

The homepage must include the literal sentences `本阶段没有运行 Qwen3-TTS 训练。` and `CANN 8.5.2 兼容性：unknown，待真机验证。`. Every page has at least one objective, prerequisite `熟悉 PyTorch 单卡张量与训练循环`, and a four-state legend.

The catalog uses only these block types: `paragraph` (`text`, `state`, `evidence_ids`), `call_chain` (`items`), `table` (`headers`, `rows`), `source_refs` (`evidence_ids`), and `index_table` (`dataset`: `files|symbols|configs`). Raw HTML is not accepted.

- [ ] **Step 4: 实现 shared partial renderer and build CLI**

Create `scripts/site_builder.py` with HTML escaping on every catalog/index value. Reuse the existing DOM contracts exactly: `chapter-nav`, `article-content`, `evidence-rail`, `toggle-left`, `toggle-right`, `site-search`, `chapter-tree`, `page-toc`, evidence cards, drawer buttons and `assets/app.js`. Compute asset/search/nav links with `posixpath.relpath`, set `aria-current="page"`, generate one `h1`, and emit previous/next links from sorted `order` only when the neighbor exists in loaded catalogs.

```python
def script_safe_json(data: object) -> str:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))


def build_site(output_root: Path, catalog_paths: list[Path]) -> list[Path]:
    pages = load_page_catalogs(catalog_paths)
    navigation = tuple(sorted(pages, key=lambda page: page["order"]))
    documents = build_search_documents(pages, load_all_indexes())
    written = []
    for page in navigation:
        target = output_root / page["slug"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(page, navigation, load_all_evidence(), documents), encoding="utf-8")
        written.append(target)
    search_path = output_root / "assets/search-index.json"
    search_path.parent.mkdir(parents=True, exist_ok=True)
    search_path.write_text(json.dumps(documents, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    written.append(search_path)
    return written
```

Create `scripts/build_site.py` with repeatable `--output` and `--catalog` arguments. Default catalogs are the foundation file plus architecture/training files only when those files exist; the command prints page/document counts and never reads ignored source roots.

- [ ] **Step 5: 增加 inline local search enhancement**

Modify `site/assets/app.js` after retaining all current controllers. `SearchController` reads `<script id="search-data" type="application/json">` on `search.html`, normalizes query with `trim().toLocaleLowerCase()`, matches whitespace-separated terms against `title + summary + headings + path + qualname + key`, and renders links with `textContent` rather than `innerHTML`.

```javascript
renderResults(query) {
  if (!this.results || !this.data) return;
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const matches = this.data.filter((item) => terms.every((term) => item.searchable.includes(term))).slice(0, 100);
  this.results.replaceChildren(...matches.map((item) => {
    const link = this.document.createElement('a');
    link.href = item.href;
    link.textContent = `${item.title} · ${item.kind}`;
    return link;
  }));
  this.resultsStatus.textContent = terms.length ? `找到 ${matches.length} 条结果` : '请输入关键词';
}
```

`search.html` embeds the same documents as `site/assets/search-index.json`; runtime never fetches remote or local JSON, so `file://` search remains functional. Preserve the no-script page link list.

Extend the existing `SearchController` constructor with `windowRef = window`, store `this.window`, `this.data`, `this.results`, and `this.resultsStatus`, then initialize query state before registering later interactions. This closes the direct-link contract used by Playwright:

```javascript
const query = new URLSearchParams(this.window.location.search).get('q') ?? '';
if (this.input) this.input.value = query;
this.renderResults(query);
this.form?.addEventListener('submit', (event) => {
  if (!this.data) return;
  event.preventDefault();
  const value = this.input?.value ?? '';
  const url = new URL(this.window.location.href);
  if (value.trim()) url.searchParams.set('q', value); else url.searchParams.delete('q');
  this.window.history.replaceState({}, '', url);
  this.renderResults(value);
});
```

- [ ] **Step 6: 扩展既有 styles，不改变视觉令牌**

Modify `theme.css` only for `.status-grid`, `.contract-table`, `.index-table`, `.search-results`, `.evidence-state`; modify `layout.css` so tables use an overflow wrapper, search results reflow at 390px, and print retains fixed URLs/evidence while hiding controls. Do not change the approved root colors, widths, 720/1200 breakpoints or localStorage keys.

- [ ] **Step 7: 构建并验证 foundation pages**

Run:

```bash
python3 -m unittest tests.test_site_builder -v
python3 scripts/build_site.py --output site --catalog content/site-foundation.json
```

Expected: 4 tests pass; CLI prints `built 4 pages and 1 search index`; the four HTML files and search JSON are created deterministically; malicious `</script>` input is encoded as `\u003c/script`.

- [ ] **Step 8: 提交 generator foundation**

```bash
git add content/site-foundation.json scripts/site_builder.py scripts/build_site.py tests/test_site_builder.py site/index.html site/indexes site/search.html site/assets/app.js site/assets/theme.css site/assets/layout.css site/assets/search-index.json
git commit -m "feat: generate knowledge site foundation"
```

Expected: one commit; no target architecture/training page exists yet, and every emitted local link points to one of the four current pages.

### Task 6: 编写 package、模型、tokenizer 与 processor 五页 target walkthrough

**Files:**
- Create: `content/target-architecture.json`
- Modify: `tests/test_site_builder.py`
- Create: `site/target/package-inference-api.html`
- Create: `site/target/model-architecture.html`
- Create: `site/target/tokenizer-12hz.html`
- Create: `site/target/tokenizer-25hz.html`
- Create: `site/target/processor-contracts.html`
- Modify: foundation HTML pages and `site/assets/search-index.json` through the generator

**Interfaces:**
- Consumes: evidence IDs `TGT-PKG-*`, `TGT-API-*`, `TGT-CONFIG-*`, `TGT-MODEL-*`, `TGT-TOK12-*`, `TGT-TOK25-*`, `TGT-PROC-*`; source index line/symbol records; shared renderer block schema.
- Produces: five independently navigable target architecture pages, fixed SHA source links, and page orders 2–6 in the 13-page sequence.

- [ ] **Step 1: 扩展 failing catalog tests**

Append:

```python
    def test_architecture_catalog_covers_required_target_symbols(self):
        paths = [ROOT / "content/site-foundation.json", ROOT / "content/target-architecture.json"]
        pages = load_page_catalogs(paths)
        self.assertEqual(len(pages), 9)
        serialized = json.dumps(pages, ensure_ascii=False)
        for symbol in ["Qwen3TTSModel.from_pretrained", "Qwen3TTSForConditionalGeneration", "Qwen3TTSTalkerForConditionalGeneration", "forward_sub_talker_finetune", "Qwen3TTSSpeakerEncoder", "Qwen3TTSTokenizerV2Model", "Qwen3TTSTokenizerV1Model", "Qwen3TTSProcessor"]:
            self.assertIn(symbol, serialized)
```

- [ ] **Step 2: 运行 test 并确认 architecture catalog 缺失**

Run: `python3 -m unittest tests.test_site_builder.SiteBuilderTest.test_architecture_catalog_covers_required_target_symbols -v`

Expected: FAIL with `FileNotFoundError: content/target-architecture.json`.

- [ ] **Step 3: 写入五页 coverage-driven catalog**

Create `content/target-architecture.json` using only renderer block types and the following exact page contracts:

| Order / slug | Sections, call flow and mandatory boundary |
| --- | --- |
| `2 / target/package-inference-api.html` | `package-layout`: exports/CLI/examples/dependencies; `load-chain`: `Qwen3TTSModel.from_pretrained → AutoConfig.register → AutoModel.from_pretrained → AutoProcessor.from_pretrained`; `base-api`: prompt creation → voice clone generation; `voice-design-api`; `custom-api`; boundary: examples require external weights/audio and are not automated tests |
| `3 / target/model-architecture.html` | `composite-config`: speaker/code-predictor/talker/top config nesting; `speaker-encoder`: 24kHz 128-bin mel → speaker embedding; `talker`: text projection + codec embedding → Qwen3 decoder → codec-0 logits; `code-predictor`: hidden state + prior codebooks → remaining 15 groups; `generation-flow`: prompt → Talker → MTP → tokenizer; boundary: static call map, no tensor/numerical run |
| `4 / target/tokenizer-12hz.html` | `configuration`; `encode-contract`: 12.5 FPS/16 codebooks is source/report claim with state labels; `rvq`: `SplitResidualVectorQuantizer`; `decode-contract`: `Qwen3TTSTokenizerV2Decoder.forward/chunked_decode`; `training-gap`: tokenizer training/discriminator/loss are not public in this tree |
| `5 / target/tokenizer-25hz.html` | `configuration`; `encoder-vq`; `dit-mel`; `bigvgan-waveform`; `asset-boundary`: official collection lacks fixed public 25Hz tokenizer checkpoint and external extractor assets are required; mark runtime statements `pending_hardware`, not verified |
| `6 / target/processor-contracts.html` | `text-contract`: Qwen tokenizer/ChatML/BatchFeature; `audio-wrapper`: normalize URL/path/base64/array then encode/decode; `shape-contract`: text ids, `(T,16)` 12Hz codes, sample-rate/downsample metadata; `prompt-contract`: x-vector-only versus ICL text+audio; `migration-boundary`: no Ascend claim |

Each page must contain: one learning objective list; prerequisite `熟悉 PyTorch 单卡张量与自回归生成`; at least two evidence-linked claim blocks; one call-chain block; a source table with exact target paths; a status/boundary section. The 25Hz page must visibly show both `已证实：静态源码存在` and `待真机验证：公开可执行性 unknown`.

- [ ] **Step 4: 构建九页并检查 immutable source links**

Run:

```bash
python3 -m unittest tests.test_site_builder -v
python3 scripts/build_site.py --output site --catalog content/site-foundation.json --catalog content/target-architecture.json
rg -n 'https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/' site/target
```

Expected: 5 tests pass; CLI prints `built 9 pages and 1 search index`; every target page has at least one fixed-SHA link and no moving `/main/` source link.

- [ ] **Step 5: 检查页面长度和证据状态**

Run:

```bash
for page in site/target/package-inference-api.html site/target/model-architecture.html site/target/tokenizer-12hz.html site/target/tokenizer-25hz.html site/target/processor-contracts.html; do test "$(rg -c '<h1' "$page")" -eq 1; test "$(rg -c 'data-evidence-state=' "$page")" -ge 2; done
rg -n 'CANN 8\.5\.2.*(兼容|支持|跑通)' site/target && exit 1 || true
```

Expected: all shell assertions exit 0; the forbidden compatibility-claim scan has no output.

- [ ] **Step 6: 提交 target architecture pages**

```bash
git add content/target-architecture.json tests/test_site_builder.py site
git commit -m "docs: add Qwen3-TTS target architecture walkthrough"
```

Expected: one commit; generated page count is 9 and navigation order is homepage → five architecture pages → three index/search pages.

### Task 7: 编写 official SFT、export 与 coverage/gaps 四页 walkthrough

**Files:**
- Create: `content/target-training.json`
- Modify: `tests/test_site_builder.py`
- Create: `site/target/sft-data-collate.html`
- Create: `site/target/sft-training-loop.html`
- Create: `site/target/optimizer-checkpoint-export.html`
- Create: `site/target/coverage-gaps.html`
- Modify: all generated HTML pages and `site/assets/search-index.json` through the generator

**Interfaces:**
- Consumes: `TGT-SCOPE-*`, `TGT-DATA-*`, `TGT-TRAIN-*`, `TGT-EXPORT-*`, `TGT-GAP-*`, `TGT-HW-*`, 35-row coverage matrix and approved reference roles.
- Produces: page orders 7–10; exact data/collate/training/export call flows; target-vs-reference gap matrix that links later-plan interfaces without implementing them.

- [ ] **Step 1: 写入 failing training coverage test**

Append:

```python
    def test_full_catalog_has_thirteen_pages_and_required_training_sections(self):
        catalogs = [ROOT / "content/site-foundation.json", ROOT / "content/target-architecture.json", ROOT / "content/target-training.json"]
        pages = load_page_catalogs(catalogs)
        self.assertEqual([page["order"] for page in pages], list(range(1, 14)))
        serialized = json.dumps(pages, ensure_ascii=False)
        for text in ["finetuning/README.md", "TTSDataset.collate_fn", "main_loss + 0.3 * sub_talker_loss", "Accelerator", "AdamW", "speaker row 3000", "CANN 8.5.2 兼容性：unknown"]:
            self.assertIn(text, serialized)
```

- [ ] **Step 2: 运行 test 并确认 training catalog 缺失**

Run: `python3 -m unittest tests.test_site_builder.SiteBuilderTest.test_full_catalog_has_thirteen_pages_and_required_training_sections -v`

Expected: FAIL with `FileNotFoundError: content/target-training.json`.

- [ ] **Step 3: 写入四页 official training catalog**

Create `content/target-training.json` with these exact contracts:

| Order / slug | Sections, call flow and mandatory boundary |
| --- | --- |
| `7 / target/sft-data-collate.html` | `public-recipe`: only 12Hz Base single-speaker; `jsonl-contract`: `audio/text/ref_audio`, then offline `audio_codes`; `offline-codes`: `prepare_data.main`; `dataset-item`: text ids + `(T,16)` codes + 24kHz/128-bin ref mel; `collate-contract`: dual `(B,T,2)` input, `(B,T,16)` codec ids, masks and codec-0 labels; no distributed sampler/bucketing claim |
| `8 / target/sft-training-loop.html` | `setup`: model/config/dataset/dataloader; `embedding-flow`: text + codec + speaker position 6 + residual embeddings; `main-forward`: codec-0 labels; `sub-talker`: selected hidden states/codes; `training-loop`: `main_loss + 0.3 * sub_talker_loss → accelerator.backward → clip → AdamW.step`; no scheduler/validation/resume and no successful-run claim |
| `9 / target/optimizer-checkpoint-export.html` | `accelerate`: BF16, accumulation 4, main-process ownership; `optimizer`: AdamW lr/weight decay and clip 1.0; `epoch-export`: copy base directory; `custom-speaker`: rewrite `tts_model_type`, speaker id 3000, drop speaker encoder, inject embedding; `checkpoint-gap`: inference-oriented safetensors, not full optimizer/RNG fault resume |
| `10 / target/coverage-gaps.html` | `target-coverage`: render all 35 file dispositions; `reference-roles`: MindSpeed-MM exact 12Hz NPU SFT anchor, MindSpeed-LLM text scale satellite, MOSS speech/codec contrast, without combining capabilities; `environment-lanes`: exact two-lane table; `future-validation`: import/device, operator/numerics, loss parity, audio/codec, checkpoint/inference, 8-card, multi-node, quality; `deferred-plans`: full reference walkthroughs, migration mapping, NPU execution |

The coverage page must distinguish documentation complete, source statically verified, project claim and hardware pending. It must say `本页不是迁移方案` and `本研究没有运行 CUDA、NPU、训练、推理或评测`. The project-native lane must not be described as reproduced, and target lane must remain unknown.

- [ ] **Step 4: 构建完整 13-page site**

Run:

```bash
python3 -m unittest tests.test_site_builder -v
python3 scripts/build_site.py --output site --catalog content/site-foundation.json --catalog content/target-architecture.json --catalog content/target-training.json
```

Expected: 6 tests pass; CLI prints `built 13 pages and 1 search index`; orders are exactly 1 through 13 with distinct previous/next destinations.

- [ ] **Step 5: 验证 no-silent-omission 页面输出**

Run:

```bash
test "$(rg -c 'data-coverage-path=' site/target/coverage-gaps.html)" -eq 35
rg -n 'MindSpeed-MM.*codeload archive|MindSpeed-LLM.*codeload archive' site/indexes/source-files.html
rg -n 'MindSpeed-MM.*clone|MindSpeed-LLM.*clone' site && exit 1 || true
rg -n '本页不是迁移方案|本研究没有运行 CUDA、NPU、训练、推理或评测|CANN 8.5.2 兼容性：unknown' site/target/coverage-gaps.html
```

Expected: 35 coverage rows; both archives are labeled `codeload archive`; no archive is called a clone; all three boundary sentences are present.

- [ ] **Step 6: 提交 target training pages**

```bash
git add content/target-training.json tests/test_site_builder.py site
git commit -m "docs: add official target SFT walkthrough"
```

Expected: one commit with the complete 13-page generated site; no candidate source or hardware result is added.

### Task 8: 建立 link/search/offline/coverage 与 Playwright completion gates

**Files:**
- Modify: `scripts/phase2_contracts.py`
- Modify: `scripts/validate_phase2.py`
- Modify: `tests/test_phase2_contracts.py`
- Modify: `tests/site/template-structure.spec.js`
- Modify: `tests/site/final-review-regressions.spec.js`
- Modify: `tests/site/template-visual.spec.js`
- Modify: `tests/site/template-visual.spec.js-snapshots/desktop-template-chromium-darwin.png`
- Modify: `tests/site/template-visual.spec.js-snapshots/laptop-template-chromium-darwin.png`
- Modify: `tests/site/template-visual.spec.js-snapshots/mobile-template-chromium-darwin.png`
- Create: `tests/site/phase2-navigation-search.spec.js`
- Create: `tests/site/phase2-responsive-accessibility.spec.js`

**Interfaces:**
- Consumes: complete 13-page site, content catalogs, 4 indexes, 22 evidence records, 35 coverage rows and existing Playwright shell behavior.
- Produces: `validate_generated_site(site_root: Path, catalogs: list[Path]) -> list[str]`, `validate_fixed_links(...)`, `validate_public_tracking(...)`; final `validate_phase2.py` gate and 49 Playwright regressions.

- [ ] **Step 1: 写入 Python failing site validation tests**

Append tests that copy generated HTML to a temporary directory, delete one target page and assert a broken-link error; mutate an `aria-controls` target and assert an ARIA error; insert `<script src="https://example.com/x.js">` and assert remote-runtime rejection; remove one coverage row and assert an omission. Use exact expected messages:

```python
self.assertIn("index.html: broken local link target/removed.html", errors)
self.assertIn("index.html: aria-controls missing-node has no matching id", errors)
self.assertIn("index.html: remote runtime resource https://example.com/x.js", errors)
self.assertIn("target coverage: missing qwen_tts/inference/qwen3_tts_model.py", errors)
```

- [ ] **Step 2: 实现 stdlib HTML/link/heading/ARIA/offline validators**

Use `html.parser.HTMLParser` to collect tags, ids, headings, href/src/link rel and ARIA references. For every one of 13 pages require: one `h1`; heading levels never jump by more than one; all relative href targets and fragments exist; all `aria-controls` values resolve; all runtime `script`, stylesheet, font, image and search data URLs are local; external anchor citations are allowed only over `https`; evidence status is in the four-state enum. Compare every generated HTML/JSON byte-for-byte with a temporary `build_site()` output to detect stale artifacts.

Extend `validate_phase2.py` success output to exactly:

```text
validated Phase 2: 4 indexes / 3270 files, 22 evidence records, 35 coverage rows, 13 pages, 0 broken links, 0 omissions
```

- [ ] **Step 3: 泛化 existing template tests to generated homepage**

Update old HCCL/MindSpeed-specific assertions, not the stable shell behavior. `template-structure.spec.js` keeps semantic regions, one h1, local resources, tokens and no-script evidence. `final-review-regressions.spec.js` uses target commit constant `022e286b98fbec7e1e916cb940cdf532cd9f488e`, expects a Qwen fixed blob URL and copies a short Qwen excerpt; all rail, drawer, tree, print and 200% tests remain. `template-visual.spec.js` continues the 1440×900, 1024×768 and 390×844 homepage baselines.

- [ ] **Step 4: 写入 multi-page navigation/search tests**

Create `tests/site/phase2-navigation-search.spec.js` with five tests:

```javascript
import { expect, test } from '@playwright/test';

test('all thirteen pages are reachable through chapter navigation', async ({ page }) => {
  await page.goto('/site/');
  await expect(page.locator('#chapter-tree a[data-page-link]')).toHaveCount(13);
});

test('previous and next links form a non-cyclic ordered path', async ({ page }) => {
  await page.goto('/site/target/model-architecture.html');
  await expect(page.getByRole('navigation', { name: '相邻章节' }).getByRole('link').first()).toHaveAttribute('href', 'package-inference-api.html');
  await expect(page.getByRole('navigation', { name: '相邻章节' }).getByRole('link').last()).toHaveAttribute('href', 'tokenizer-12hz.html');
});

test('inline search finds a symbol without network fetch', async ({ page }) => {
  const requests = [];
  page.on('request', (request) => requests.push(request.url()));
  await page.goto('/site/search.html?q=forward_sub_talker_finetune');
  await expect(page.getByRole('status')).toContainText('找到');
  await expect(page.getByRole('link', { name: /forward_sub_talker_finetune/ })).toBeVisible();
  expect(requests.every((url) => new URL(url).origin === new URL(page.url()).origin)).toBe(true);
});

test('file and config indexes expose all snapshots without source bodies', async ({ page }) => {
  await page.goto('/site/indexes/source-files.html');
  await expect(page.locator('[data-snapshot-id]')).toHaveCount(4);
  await page.goto('/site/indexes/symbols-configs.html');
  await expect(page.getByText('Qwen3TTSForConditionalGeneration', { exact: true })).toBeVisible();
  await expect(page.locator('[data-source-body]')).toHaveCount(0);
});

test('coverage page exposes all target dispositions and future interfaces', async ({ page }) => {
  await page.goto('/site/target/coverage-gaps.html');
  await expect(page.locator('[data-coverage-path]')).toHaveCount(35);
  await expect(page.getByText('MindSpeed-MM 完整走读')).toBeVisible();
  await expect(page.getByText(/CANN 8.5.2.*unknown/)).toBeVisible();
});
```

- [ ] **Step 5: 写入 responsive/accessibility/offline tests**

Create `tests/site/phase2-responsive-accessibility.spec.js` with five tests: axe WCAG A/AA on `model-architecture.html` at 1440×900; axe on `sft-data-collate.html` at 1024×768; axe plus both drawers on `coverage-gaps.html` at 390×844; JavaScript-disabled traversal that still sees article/evidence/fixed links; 720px layout viewport/200% reflow with wide coverage/index tables and no document-level horizontal overflow. Every axe assertion prints the full violation JSON on failure.

- [ ] **Step 6: 运行 Python validators and suites**

Run:

```bash
python3 scripts/validate_phase2.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Expected: exact validator success line shown above; 36 Python tests pass; whitespace check has no output.

- [ ] **Step 7: 更新并复验三视口 screenshots**

Run:

```bash
npm run test:update-snapshots -- tests/site/template-visual.spec.js
npm test -- tests/site/template-visual.spec.js
```

Expected: three homepage snapshots update once; the second command reports 3 passed with no diff.

- [ ] **Step 8: 运行完整 Playwright suite**

Run: `npm test`

Expected: 49 tests pass: the existing 39 shell regressions (with content-specific assertions generalized) plus 10 Phase 2 multi-page/search/responsive/accessibility tests.

- [ ] **Step 9: 运行 final public-content and actual-path audit**

Run:

```bash
git ls-files | rg '(^|/)\.superpowers/source-checkouts/|\.(safetensors|ckpt|pt|pth|onnx|gguf|wav|mp3|m4a|flac)$|(^|/)(weights|datasets|checkpoints)(/|$)' && exit 1 || true
rg -ni 'to''do|tb''d|place''holder|lorem'' ipsum' content research/indexes research/target-evidence.json research/target-coverage.csv site scripts tests
rg -n '/Users/|[A-Za-z]:\\\\' research/indexes site/assets/search-index.json
for path in finetuning/README.md finetuning/dataset.py finetuning/sft_12hz.py qwen_tts/core/models/modeling_qwen3_tts.py qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py; do test -f ".superpowers/source-checkouts/qwen3-tts-022e286b/$path"; done
git status --short
```

Expected: restricted tracking, placeholder and absolute-path scans have no output; all six verified target paths exist; status lists only Task 8 intended files before commit.

- [ ] **Step 10: 提交 completion gates**

```bash
git add scripts/phase2_contracts.py scripts/validate_phase2.py tests/test_phase2_contracts.py tests/site
git commit -m "test: verify Phase 2 target walkthrough"
```

Expected: one commit; `python3 scripts/validate_phase2.py`, Python tests and 49 Playwright tests remain green; no push occurs.

## Completion Verification

Immediately before reporting Phase 2 implementation complete, run:

```bash
python3 scripts/validate_phase2.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
npm test
git diff --check
git status -sb
git ls-files | rg '(^|/)\.superpowers/source-checkouts/|\.(safetensors|ckpt|pt|pth|onnx|gguf|wav|mp3|m4a|flac)$|(^|/)(weights|datasets|checkpoints)(/|$)' && exit 1 || true
```

Required evidence:

- Four deterministic indexes validate at exact revisions and total 3,270 materialized files; archive inputs were never described or handled as Git repositories.
- 22 bounded evidence records use all four states; 35 target files have exactly one mapped/excluded/pending disposition.
- The generated site has exactly 13 coverage-driven pages, one `h1` each, complete previous/next navigation, local inline search and no broken local links/fragments.
- Python suite reports 36 passed; Playwright reports 49 passed across desktop, laptop, mobile, 200% reflow, no-script and axe cases.
- No tracked source tree, weight, dataset, checkpoint, LFS object, secret, restricted media, absolute local path or full source body exists.
- The content visibly preserves PyTorch single-card teaching, both environment lanes, CANN 8.5.2 unknown status and all deferred later-plan boundaries.
