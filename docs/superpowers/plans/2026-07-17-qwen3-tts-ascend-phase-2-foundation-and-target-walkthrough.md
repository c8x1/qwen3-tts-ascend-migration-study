# Qwen3-TTS Ascend Phase 2 Foundation and Target Walkthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立四个固定源码快照的可复现元数据索引，并在既有静态站模板上发布一组从 PyTorch 单卡基础出发、证据可追溯的 Qwen3-TTS 官方目标侧多页源码走读。

**Architecture:** 一个只依赖 Python 标准库的索引器从显式 `--source-root` 读取只读目录；acquisition handoff/registry 提供并固定 Git/archive identity，索引器只校验调用方声明并计算物化内容 digest，不把 digest 冒充 Git identity。另一个标准库生成器把结构化页面内容、证据记录、覆盖矩阵和这些索引渲染为复用现有 `site/index.html`、`site/assets/{theme.css,layout.css,app.js}` 交互契约的多页静态站；站点通过本地 HTTP 提供，浏览器断网后不发出外部请求，Python 验证器和 Playwright 共同守住可追溯、无遗漏、导航、搜索、ARIA 与响应式边界。

**Tech Stack:** Python 3.11+ 标准库（`argparse`、`ast`、`csv`、`hashlib`、`html`、`json`、`pathlib`、`tomllib`、`unittest`、`html.parser`）、HTML5、CSS3、原生 ES modules、Node.js 24、Playwright 1.61.1、axe-core Playwright 4.12.1。

## Global Constraints

- 本阶段只做索引基础、Qwen3-TTS 官方目标侧走读和静态站验证；不修改任一候选源码，不运行模型、训练、推理、转换、评测或 Ascend 910B smoke。
- 公开仓库永不追踪源码树、模型权重、数据集、checkpoint、Git LFS object、密钥、令牌或受限媒体；只追踪 acquisition metadata、文件/符号/配置索引、必要短引用、固定链接和生成 HTML。
- 四个本地输入一律只读：Qwen3-TTS `022e286b...` 与 MOSS-TTS `ad99ec5f...` 是 sparse Git checkout；MindSpeed-MM `0edd553e...` 与 MindSpeed-LLM `434baff7...` 是 codeload archive snapshot，绝不称为 clone 或 checkout。
- 索引 CLI 必须显式接收 `--source-root`、`--snapshot-id`、`--revision`、`--output`；不得读取或要求 `.git`，不得写入输入树，输出必须对相同物化目录逐字节确定。
- 本阶段不使用 GitNexus：它要求 Git repository，并会写 `.gitnexus`/context 文件；两个入选快照是 archive，四个输入又都必须只读。以后若确有图谱价值，只能在一次性、可删除、真实 Git index workspace 中另行评估。
- 测试只读取 `tests/fixtures/source-index/` 小型 fixture，不读取 ignored source checkouts；真实四树 generation 是独立、可跳过的本地命令，机器没有 checkout 时不阻断 fixture 单元测试。
- 追踪的 index 不得含绝对本地路径、`source_root`、源码正文或无限长 quote；每个输出记录 snapshot id、完整 revision、content identity、每文件 SHA-256 和全索引 digest。
- 站点继续使用现有暖纸张三栏 shell、侧栏状态机、抽屉、复制与视觉令牌，不重新设计；offline 的操作定义是“由 `http://127.0.0.1` 本地 HTTP server 提供生成站点，然后浏览器 `context.setOffline(true)`”，所有运行时 CSS/JavaScript/搜索数据都在站内，断网时无外部请求；不承诺 `file://` JavaScript 行为，禁用 JavaScript 时仍有正文和静态目录链接。
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
| `research/schemas/target-evidence.schema.json` | source/ledger/file-only evidence、source IDs 与内部 decision refs 的严格结构 |
| `research/schemas/page-catalog.schema.json` | 13 页目录、section 与五类 renderer block 的 tagged-union contract |
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
| `IMPLEMENTATION_NOTES.md` | Task 3 记录 acquisition/index identity 限制；Task 8 记录 Phase 2 完成范围、实现偏差与 deferred work |

### Task 1: 固化四快照 identity 与 source-index schema

**Files:**
- Create: `research/source-snapshots.json`
- Create: `research/schemas/source-index.schema.json`
- Create: `scripts/phase2_contracts.py`
- Create: `tests/test_phase2_contracts.py`

**Interfaces:**
- Consumes: four Phase 1 acquisition handoffs and the already inspected read-only trees.
- Produces: `load_snapshot_registry(path: Path) -> dict[str, Snapshot]`, `validate_snapshot_registry(data: object) -> list[str]`, `validate_source_index(data: object, registry: dict[str, Snapshot]) -> list[str]`; immutable `Snapshot(snapshot_id, project, role, revision, acquisition_kind, content_id, materialized_file_count, blob_url_template, excluded_paths, gitlinks)`.

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
        self.assertEqual(snapshots["qwen3-tts-022e286b"].excluded_paths,
                         (".github/.DS_Store", "assets/Qwen3_TTS.pdf"))
        self.assertEqual(len(snapshots["moss-tts-ad99ec5f"].excluded_paths), 18)
        self.assertEqual(snapshots["moss-tts-ad99ec5f"].gitlinks,
                         ({"path": "moss_audio_tokenizer", "revision": "56776e867cb38446fa4bc00d0aceccab5001b008", "initialized": False},))

    def test_registry_rejects_local_paths_and_git_claim_for_archives(self):
        data = json.loads((ROOT / "research/source-snapshots.json").read_text())
        data["snapshots"][1]["local_path"] = "/Users/example/archive"
        data["snapshots"][1]["acquisition_kind"] = "git-clone"
        errors = validate_snapshot_registry(data)
        self.assertIn("snapshots[1]: unknown field local_path", errors)
        self.assertIn("snapshots[1].acquisition_kind: expected codeload-archive", errors)

    def test_registry_rejects_unknown_or_incomplete_identity_and_bad_relative_paths(self):
        data = json.loads((ROOT / "research/source-snapshots.json").read_text())
        data["snapshots"][0]["snapshot_id"] = "unknown-snapshot"
        data["snapshots"][1]["project"] = ""
        data["snapshots"][2]["materialized_file_count"] = -1
        data["snapshots"][3]["excluded"]["paths"] = ["../escape", "../escape"]
        errors = validate_snapshot_registry(data)
        self.assertIn("snapshots[0].snapshot_id: unapproved unknown-snapshot", errors)
        self.assertIn("snapshots[1].project: expected non-empty string", errors)
        self.assertIn("snapshots[2].materialized_file_count: expected nonnegative integer", errors)
        self.assertIn("snapshots[3].excluded.paths: duplicate path", errors)
        self.assertIn("snapshots[3].excluded.paths: expected relative POSIX path ../escape", errors)
        self.assertTrue(any(error.startswith("registry.snapshots: expected approved IDs") for error in errors))
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
      "excluded": {"paths": [".github/.DS_Store", "assets/Qwen3_TTS.pdf"], "reason": "sparse source-only checkout excludes rendered paper and macOS metadata"},
      "gitlinks": []
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
      "excluded": {"paths": [], "reason": "exact-SHA codeload tree; no Git metadata retained"},
      "gitlinks": []
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
      "excluded": {"paths": [], "reason": "tree-hash-verified exact-SHA codeload tree; no Git metadata retained"},
      "gitlinks": []
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
      "excluded": {
        "paths": [
          "assets/audio/reference_02_s1.wav", "assets/audio/reference_02_s2.wav", "assets/audio/reference_en.m4a",
          "assets/audio/reference_en_0.mp3", "assets/audio/reference_en_1.mp3", "assets/audio/reference_en_2.mp3",
          "assets/audio/reference_en_3.mp3", "assets/audio/reference_zh.wav", "assets/audio/reference_zh_0.wav",
          "assets/audio/reference_zh_1.wav", "assets/audio/reference_zh_2.wav", "assets/audio/reference_zh_3.mp3",
          "assets/text/moss_tts_example_texts.jsonl", "assets/text/moss_voice_generator_example_texts.jsonl",
          "moss_tts_realtime/audio/prompt_audio.mp3", "moss_tts_realtime/audio/prompt_audio1.mp3",
          "moss_tts_realtime/audio/user1.wav", "moss_tts_realtime/audio/user2.wav"
        ],
        "reason": "source-only sparse checkout excludes committed wav/mp3/m4a/jsonl assets"
      },
      "gitlinks": [{"path": "moss_audio_tokenizer", "revision": "56776e867cb38446fa4bc00d0aceccab5001b008", "initialized": false}]
    }
  ]
}
```

- [ ] **Step 4: 写入允许字段严格的 JSON schema**

Create `research/schemas/source-index.schema.json` with `additionalProperties: false` at root, snapshot, file, symbol and config levels. The root required fields are `schema_version`, `snapshot`, `indexer_version`, `files`, `symbols`, `configs`, `content_digest`; file fields are `path`, `bytes`, `sha256`, `kind`, `line_count`; symbol fields are `id`, `path`, `qualname`, `name`, `kind`, `line`, `end_line`; config fields are `id`, `path`, `key`, `owner`, `kind`, `line`. `line_count` is an integer `>=0` for all text-like kinds and `null` for binary. Do not define `source_root`, `body`, `source`, `text`, or `generated_at`.

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
    "files": {"type": "array", "items": {"type": "object", "additionalProperties": false, "required": ["path", "bytes", "sha256", "kind", "line_count"], "properties": {
      "path": {"type": "string"}, "bytes": {"type": "integer", "minimum": 0}, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "kind": {"enum": ["python", "json", "toml", "yaml", "text", "binary"]}, "line_count": {"type": ["integer", "null"], "minimum": 0}
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

Create `scripts/phase2_contracts.py` with the public types below. The implementation must recursively validate the same allowed/required/type/enum/const/pattern/minimum constraints encoded in `source-index.schema.json`; the schema is loaded and used by `validate_source_index`, not merely committed as documentation. Validation is total over JSON values: a malformed root, nested snapshot, list container, or row produces stable path-prefixed errors and never raises `AttributeError`, `KeyError`, `TypeError`, or a sort exception. After structural validation succeeds, apply semantic checks for `line <= end_line`, text/binary `line_count`, unique IDs, declared registry identity, deterministic sort order, materialized-content digest, and both POSIX and Windows absolute paths.

```python
from __future__ import annotations

import json
import hashlib
import collections
import csv
import re
import tempfile
import urllib.parse
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACQUISITION = {
    "qwen3-tts-022e286b": "git-sparse-checkout",
    "mindspeed-mm-0edd553e": "codeload-archive",
    "mindspeed-llm-434baff7": "codeload-archive",
    "moss-tts-ad99ec5f": "git-sparse-checkout",
}
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
    excluded_paths: tuple[str, ...]
    gitlinks: tuple[dict[str, object], ...]


def _is_absolute(value: str) -> bool:
    return value.startswith(("/", "\\\\")) or bool(re.match(r"^[A-Za-z]:[\\/]", value))


def _validate(node: object, schema: dict[str, object], path: str, errors: list[str]) -> None:
    """Recursive subset of Draft 2020-12 used by source-index.schema.json.

    Check type before any container operation; then additionalProperties,
    required, properties/items, enum/const/pattern/minimum in that order so
    malformed inputs always produce stable messages.
    """
    if "oneOf" in schema:
        base_schema = {key: value for key, value in schema.items() if key != "oneOf"}
        _validate(node, base_schema, path, errors)
        branch_results = []
        for branch in schema["oneOf"]:
            branch_errors: list[str] = []
            _validate(node, branch, path, branch_errors)
            branch_results.append(branch_errors)
        if sum(not branch for branch in branch_results) != 1:
            errors.append(f"{path}: expected exactly one oneOf branch")
        return
    expected = schema.get("type")
    allowed = expected if isinstance(expected, list) else [expected] if expected else []
    matches = any(
        (kind == "object" and isinstance(node, dict)) or
        (kind == "array" and isinstance(node, list)) or
        (kind == "string" and isinstance(node, str)) or
        (kind == "integer" and isinstance(node, int) and not isinstance(node, bool)) or
        (kind == "null" and node is None)
        for kind in allowed
    )
    if allowed and not matches:
        errors.append(f"{path}: expected {' or '.join(allowed)}")
        return
    if "const" in schema and node != schema["const"]:
        errors.append(f"{path}: expected {schema['const']}")
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}")
    if isinstance(node, str) and schema.get("pattern") and not re.fullmatch(str(schema["pattern"]), node):
        errors.append(f"{path}: pattern mismatch")
    if isinstance(node, str) and "minLength" in schema and len(node) < schema["minLength"]:
        errors.append(f"{path}: shorter than {schema['minLength']}")
    if isinstance(node, str) and "maxLength" in schema and len(node) > schema["maxLength"]:
        errors.append(f"{path}: longer than {schema['maxLength']}")
    if isinstance(node, int) and not isinstance(node, bool) and "minimum" in schema and node < schema["minimum"]:
        errors.append(f"{path}: below minimum {schema['minimum']}")
    if isinstance(node, dict):
        properties = schema.get("properties", {})
        for key in sorted(set(schema.get("required", [])) - set(node)):
            errors.append(f"{path}: missing field {key}")
        if schema.get("additionalProperties") is False:
            for key in sorted(set(node) - set(properties)):
                errors.append(f"{path}: unknown field {key}")
        for key in sorted(set(node) & set(properties)):
            _validate(node[key], properties[key], f"{path}.{key}", errors)
    if isinstance(node, list) and "items" in schema:
        if "minItems" in schema and len(node) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in node}) != len(node):
            errors.append(f"{path}: duplicate item")
        for index, item in enumerate(node):
            _validate(item, schema["items"], f"{path}[{index}]", errors)


def validate_snapshot_registry(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["registry: expected object"]
    if data.get("schema_version") != 1:
        errors.append("registry.schema_version: expected 1")
    rows = data.get("snapshots")
    if not isinstance(rows, list):
        errors.append("registry.snapshots: expected array")
        return errors
    required = {"snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id", "materialized_file_count", "source_url", "blob_url_template", "excluded", "gitlinks"}
    seen: set[str] = set()
    for index, item in enumerate(rows):
        prefix = f"snapshots[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: expected object")
            continue
        for key in sorted(required - set(item)):
            errors.append(f"{prefix}: missing field {key}")
        for key in sorted(set(item) - required):
            errors.append(f"{prefix}: unknown field {key}")
        snapshot_id = item.get("snapshot_id")
        if not isinstance(snapshot_id, str):
            errors.append(f"{prefix}.snapshot_id: expected string")
        elif snapshot_id not in ACQUISITION:
            errors.append(f"{prefix}.snapshot_id: unapproved {snapshot_id}")
        elif snapshot_id in seen:
            errors.append(f"{prefix}.snapshot_id: duplicate {snapshot_id}")
        else:
            seen.add(snapshot_id)
        expected = ACQUISITION.get(snapshot_id)
        if expected and item.get("acquisition_kind") != expected:
            errors.append(f"{prefix}.acquisition_kind: expected {expected}")
        if not isinstance(item.get("revision"), str) or not re.fullmatch(r"[0-9a-f]{40}", item["revision"]):
            errors.append(f"{prefix}.revision: expected 40 lowercase hex")
        for key in ("project", "role", "content_id", "source_url", "blob_url_template"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{prefix}.{key}: expected non-empty string")
        count = item.get("materialized_file_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append(f"{prefix}.materialized_file_count: expected nonnegative integer")
        excluded = item.get("excluded")
        if not isinstance(excluded, dict) or set(excluded) != {"paths", "reason"} or not isinstance(excluded.get("paths"), list) or not all(isinstance(path, str) for path in excluded.get("paths", [])) or not isinstance(excluded.get("reason"), str):
            errors.append(f"{prefix}.excluded: expected paths/reason object")
        else:
            paths = excluded["paths"]
            if len(paths) != len(set(paths)):
                errors.append(f"{prefix}.excluded.paths: duplicate path")
            for path in paths:
                if not path or _is_absolute(path) or "\\" in path or ".." in path.split("/"):
                    errors.append(f"{prefix}.excluded.paths: expected relative POSIX path {path}")
        gitlinks = item.get("gitlinks")
        if not isinstance(gitlinks, list) or not all(isinstance(link, dict) and set(link) == {"path", "revision", "initialized"} and isinstance(link["path"], str) and isinstance(link["revision"], str) and bool(re.fullmatch(r"[0-9a-f]{40}", link["revision"])) and isinstance(link["initialized"], bool) for link in gitlinks):
            errors.append(f"{prefix}.gitlinks: expected path/revision/initialized records")
        else:
            paths = [link["path"] for link in gitlinks]
            if len(paths) != len(set(paths)):
                errors.append(f"{prefix}.gitlinks: duplicate path")
            for path in paths:
                if not path or _is_absolute(path) or "\\" in path or ".." in path.split("/"):
                    errors.append(f"{prefix}.gitlinks: expected relative POSIX path {path}")
    approved = set(ACQUISITION)
    if seen != approved:
        errors.append(f"registry.snapshots: expected approved IDs {','.join(sorted(approved))}")
    return errors


def load_snapshot_registry(path: Path) -> dict[str, Snapshot]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_snapshot_registry(data)
    if errors:
        raise ValueError("\n".join(errors))
    result: dict[str, Snapshot] = {}
    for item in data["snapshots"]:
        result[item["snapshot_id"]] = Snapshot(
            snapshot_id=item["snapshot_id"], project=item["project"], role=item["role"],
            revision=item["revision"], acquisition_kind=item["acquisition_kind"],
            content_id=item["content_id"], materialized_file_count=item["materialized_file_count"],
            blob_url_template=item["blob_url_template"], excluded_paths=tuple(item["excluded"]["paths"]),
            gitlinks=tuple(item["gitlinks"]),
        )
    return result


@lru_cache(maxsize=1)
def load_source_index_schema() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "research/schemas/source-index.schema.json").read_text(encoding="utf-8"))


def _walk(node: object, path: str = "index"):
    if isinstance(node, dict):
        for key in sorted(node):
            yield f"{path}.{key}", key, node[key]
            yield from _walk(node[key], f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}[{index}]")


def _materialized_digest(data: dict[str, object]) -> str:
    payload = {key: value for key, value in data.items() if key != "content_digest"}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_source_index(data: object, registry: dict[str, Snapshot]) -> list[str]:
    errors: list[str] = []
    _validate(data, load_source_index_schema(), "index", errors)
    if errors:
        return errors
    assert isinstance(data, dict)
    snapshot_data = data["snapshot"]
    snapshot_id = snapshot_data["snapshot_id"]
    snapshot = registry.get(snapshot_id)
    if snapshot is None:
        errors.append(f"index.snapshot.snapshot_id: unknown {snapshot_id}")
    else:
        for key in ("snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id"):
            if snapshot_data[key] != getattr(snapshot, key):
                errors.append(f"index.snapshot.{key}: registry mismatch")
    for value_path, key, value in _walk(data):
        if key in FORBIDDEN_KEYS:
            errors.append(f"{value_path}: forbidden field")
        if isinstance(value, str) and _is_absolute(value):
            errors.append(f"{value_path}: absolute path forbidden")
    files = data["files"]
    symbols = data["symbols"]
    configs = data["configs"]
    if files != sorted(files, key=lambda row: row["path"]):
        errors.append("index.files: not deterministically sorted")
    if symbols != sorted(symbols, key=lambda row: row["id"]):
        errors.append("index.symbols: not deterministically sorted")
    if configs != sorted(configs, key=lambda row: row["id"]):
        errors.append("index.configs: not deterministically sorted")
    file_map = {row["path"]: row for row in files}
    if len(file_map) != len(files):
        errors.append("index.files: duplicate path")
    for index, row in enumerate(files):
        expected_null = row["kind"] == "binary"
        if expected_null != (row["line_count"] is None):
            errors.append(f"index.files[{index}].line_count: binary must be null and text must be integer")
    for row_name, rows in (("symbols", symbols), ("configs", configs)):
        ids = [row["id"] for row in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"index.{row_name}: duplicate id")
        for index, row in enumerate(rows):
            owner_file = file_map.get(row["path"])
            if owner_file is None:
                errors.append(f"index.{row_name}[{index}].path: not in files")
                continue
            line_count = owner_file["line_count"]
            if line_count is None or row["line"] > line_count:
                errors.append(f"index.{row_name}[{index}].line: exceeds file line_count")
    for index, row in enumerate(symbols):
        owner_file = file_map.get(row["path"])
        if row["line"] > row["end_line"]:
            errors.append(f"index.symbols[{index}]: line exceeds end_line")
        elif owner_file is not None and isinstance(owner_file["line_count"], int) and row["end_line"] > owner_file["line_count"]:
            errors.append(f"index.symbols[{index}].end_line: exceeds file line_count")
        if row["id"] != f'{row["path"]}:{row["qualname"]}:{row["line"]}':
            errors.append(f"index.symbols[{index}].id: expected path:qualname:line")
    for index, row in enumerate(configs):
        if row["id"] != f'{row["path"]}:{row["key"]}:{row["line"]}':
            errors.append(f"index.configs[{index}].id: expected path:key:line")
    if data["content_digest"] != _materialized_digest(data):
        errors.append("index.content_digest: materialized content digest mismatch")
    return errors
```

`load_snapshot_registry()` converts nested `excluded.paths` to `excluded_paths` and preserves `gitlinks`; `load_source_index_schema()` reads `research/schemas/source-index.schema.json` once with `functools.lru_cache`. Add the following malformed-container regression matrix to `tests/test_phase2_contracts.py`:

```python
def test_source_index_validator_is_recursive_and_total(self):
    cases = [
        ({"snapshot": []}, "index.snapshot: expected object"),
        ({"snapshot": {"snapshot_id": "fixture", "extra": 1}}, "index.snapshot: unknown field extra"),
        ({"snapshot": {"snapshot_id": "fixture"}}, "index.snapshot: missing field project"),
        ({"files": {}}, "index.files: expected array"),
        ({"files": [None]}, "index.files[0]: expected object"),
        ({"symbols": [{"line": "1"}]}, "index.symbols[0].line: expected integer"),
    ]
    for mutation, expected in cases:
        with self.subTest(expected=expected):
            data = valid_minimal_index()
            data.update(mutation)
            self.assertIn(expected, validate_source_index(data, {"fixture": FIXTURE_SNAPSHOT}))

def test_rejects_windows_and_posix_absolute_paths_and_reversed_range(self):
    for bad in ["/tmp/x.py", r"C:\\src\\x.py", r"\\server\\share\\x.py"]:
        data = valid_minimal_index(file_path=bad)
        self.assertIn("absolute path forbidden", "\n".join(validate_source_index(data, {"fixture": FIXTURE_SNAPSHOT})))
    data = valid_minimal_index(symbol_line=9, symbol_end_line=4)
    self.assertIn("index.symbols[0]: line exceeds end_line", validate_source_index(data, {"fixture": FIXTURE_SNAPSHOT}))

def test_symbol_missing_or_binary_owner_returns_errors_without_crashing(self):
    missing = valid_minimal_index()
    missing["symbols"][0]["path"] = "missing.py"
    missing["symbols"][0]["id"] = "missing.py:f:1"
    refresh_materialized_digest(missing)
    self.assertIn("index.symbols[0].path: not in files", validate_source_index(missing, {"fixture": FIXTURE_SNAPSHOT}))
    binary = valid_minimal_index()
    binary["files"][0].update({"kind": "binary", "line_count": None})
    refresh_materialized_digest(binary)
    self.assertIn("index.symbols[0].line: exceeds file line_count", validate_source_index(binary, {"fixture": FIXTURE_SNAPSHOT}))
```

Define `FIXTURE_SNAPSHOT` and `valid_minimal_index()` in the same test module so every mutation begins from a complete valid container and recomputes the materialized digest before validation:

```python
from scripts.phase2_contracts import Snapshot, _materialized_digest

FIXTURE_SNAPSHOT = Snapshot("fixture", "Fixture/Source", "test", "a" * 40,
    "codeload-archive", "fixture:1", 1, "https://example.invalid/{path}#L{start}-L{end}", (), ())

def valid_minimal_index(file_path="x.py", symbol_line=1, symbol_end_line=1, snapshot=FIXTURE_SNAPSHOT):
    data = {
        "schema_version": 1,
        "snapshot": {key: getattr(snapshot, key) for key in ("snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id")},
        "indexer_version": "1.0",
        "files": [{"path": file_path, "bytes": 2, "sha256": "0" * 64, "kind": "python", "line_count": 10}],
        "symbols": [{"id": f"{file_path}:f:{symbol_line}", "path": file_path, "qualname": "f", "name": "f", "kind": "function", "line": symbol_line, "end_line": symbol_end_line}],
        "configs": [],
    }
    data["content_digest"] = _materialized_digest(data)
    return data


def refresh_materialized_digest(data):
    data["content_digest"] = _materialized_digest(data)
```

When a test mutates any digest-covered field, call `refresh_materialized_digest(data)` before asserting the targeted semantic error. Tests that target digest mismatch deliberately do not refresh it.

- [ ] **Step 6: 运行 contract tests**

Run: `python3 -m unittest tests.test_phase2_contracts -v`

Expected: all registry/schema tests pass, including nested unknown/missing/type/malformed containers, stable errors, SHA/enum/range checks and absolute-path rejection.

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
        def closure():
            self.NOT_CONFIG = 1
        closure()
        return self.width


def build(config: SampleConfig):
    LOCAL_ONLY = 99
    return config.describe()


class DuplicateNames:
    @property
    def value(self):
        return 1

    @value.setter
    def value(self, new_value):
        self.current = new_value

    def overloaded(self, value: int):
        return value

    def overloaded(self, value: str):
        return value
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
SNAPSHOT = Snapshot("fixture", "Fixture/Source", "test", "a" * 40, "codeload-archive", "fixture:1", 5, "https://example.invalid/{path}#L{start}-L{end}", (), ())


def run_cli(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([
        "python3", "scripts/build_source_index.py", "--source-root", str(source),
        "--snapshot-id", "qwen3-tts-022e286b",
        "--revision", "022e286b98fbec7e1e916cb940cdf532cd9f488e",
        "--output", str(output),
    ], cwd=ROOT, text=True, capture_output=True)


class SourceIndexTest(unittest.TestCase):
    def test_builds_files_symbols_and_config_keys_without_git(self):
        data = build_index(FIXTURE, SNAPSHOT)
        self.assertEqual(len(data["files"]), 5)
        qualnames = [row["qualname"] for row in data["symbols"]]
        self.assertTrue({"SampleConfig", "SampleConfig.__init__", "SampleConfig.describe", "build"}.issubset(qualnames))
        keys = {row["key"] for row in data["configs"]}
        self.assertTrue({"DEFAULT_RATE", "SampleConfig.model_type", "SampleConfig.width", "model.name", "training.precision"}.issubset(keys))
        self.assertNotIn("LOCAL_ONLY", keys)
        self.assertNotIn("SampleConfig.NOT_CONFIG", keys)
        symbol_ids = [row["id"] for row in data["symbols"]]
        self.assertEqual(len(symbol_ids), len(set(symbol_ids)))
        self.assertEqual(len([row for row in data["symbols"] if row["qualname"] == "DuplicateNames.value"]), 2)
        self.assertEqual(len([row for row in data["symbols"] if row["qualname"] == "DuplicateNames.overloaded"]), 2)
        self.assertTrue(all(row["id"] == f'{row["path"]}:{row["qualname"]}:{row["line"]}' for row in data["symbols"]))
        self.assertTrue(all((row["kind"] == "binary") == (row["line_count"] is None) for row in data["files"]))
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

    def test_rejects_source_root_symlink_and_output_inside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "real"
            real.mkdir()
            alias = Path(tmp) / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "source root symlink forbidden"):
                build_index(alias, SNAPSHOT)
            result = run_cli(alias, Path(tmp) / "outside.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("source root symlink forbidden", result.stderr)
            result = run_cli(real, real / "index.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("output must be outside source root", result.stderr)

    def test_extensionless_and_packaging_files_are_text_metadata(self):
        names = ["LICENSE", "Makefile", "Dockerfile", "MANIFEST.in", ".gitignore", "README"]
        self.assertEqual([file_kind(Path(name)) for name in names], ["text"] * len(names))
```

- [ ] **Step 3: 运行 tests 并确认 index library 缺失**

Run: `python3 -m unittest tests.test_source_index -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.source_index'`.

- [ ] **Step 4: 实现文件发现、hash、AST 和 config-key extraction**

Create `scripts/source_index.py`. It must never call Git and does not validate Git/archive identity: revision/acquisition/content identity come from the acquisition handoff and registry; this library only checks the caller's registry declaration and creates a digest of materialized file metadata. It prunes only `.git`, `__pycache__`, `.pytest_cache`, `node_modules`, `playwright-report`, and `test-results`, and indexes every other regular file as path/size/hash/line-count metadata. Python parsing emits classes, top-level functions and every method occurrence; symbol IDs include definition line so repeated property setter/overload/redefinition qualnames remain unique. Config extraction emits names only, never scalar values: module/class assignments plus `self.attr` in class methods, never ordinary function-local names such as `LOCAL_ONLY`.

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
    if source_root.is_symlink():
        raise ValueError("source root symlink forbidden")
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
    return {"id": f"{path}:{qualname}:{node.lineno}", "path": path, "qualname": qualname, "name": name, "kind": kind, "line": node.lineno, "end_line": node.end_lineno}


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
        self.function_depth = 0
        self.rows: list[dict[str, object]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.owners.append(node.name)
        self.generic_visit(node)
        self.owners.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

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
            if isinstance(target, ast.Name) and self.function_depth == 0 and (target.id.isupper() or target.id in {"model_type", "sub_configs"}):
                name = target.id
            elif self.owners and self.function_depth == 1 and isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
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
            rows.append({"id": f"{relative}:{dotted}:1", "path": relative, "key": dotted, "owner": prefix, "kind": kind, "line": 1})
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
        kind = file_kind(path)
        raw = path.read_bytes()
        line_count = None if kind == "binary" else len(raw.decode("utf-8", errors="replace").splitlines())
        files.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "kind": kind, "line_count": line_count})
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
    if args.source_root.is_symlink():
        parser.error("source root symlink forbidden")
    source_root = args.source_root.resolve(strict=True)
    output = args.output.resolve(strict=False)
    if output == source_root or source_root in output.parents:
        parser.error("output must be outside source root")
    data = build_index(args.source_root, snapshot)
    errors = validate_source_index(data, registry)
    if errors:
        parser.error("; ".join(errors))
    write_canonical_json(data, output)
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

Expected: all source-index tests pass; help lists all four required flags; no `.superpowers/source-checkouts` path is opened by tests; source-root and descendant symlinks are rejected before hashing; resolved output containment is rejected before writing; extensionless packaging files are text metadata; duplicate qualnames have unique `path:qualname:line` IDs; `LOCAL_ONLY` is absent. The real-tree generation in Task 3 additionally asserts the known duplicate-qualname regression inventory: MindSpeed-MM has 10 duplicate `(path, qualname)` groups and MOSS-TTS has 1, while IDs remain unique.

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
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: `build_source_index.py`, the four exact read-only roots, and the registry's expected file counts.
- Produces: four schema-v1 indexes totaling exactly 3,270 materialized files; CLI `python3 scripts/validate_phase2.py --indexes-only` and reproducibility proof by regenerating to a temporary directory.

- [ ] **Step 1: 扩展 index validation tests**

Append these tests to `tests/test_phase2_contracts.py`:

```python
import collections

from scripts.phase2_contracts import validate_source_index


class SourceIndexContractTest(unittest.TestCase):
    def test_index_rejects_absolute_path_after_schema_validation(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        data = valid_minimal_index(snapshot=registry["qwen3-tts-022e286b"])
        data["files"][0]["path"] = "/Users/me/source.py"
        data["symbols"][0]["path"] = "/Users/me/source.py"
        data["symbols"][0]["id"] = "/Users/me/source.py:f:1"
        refresh_materialized_digest(data)
        errors = validate_source_index(data, registry)
        self.assertTrue(any("absolute path forbidden" in error for error in errors))

    def test_index_rejects_unknown_body_at_schema_layer(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        data = valid_minimal_index(snapshot=registry["qwen3-tts-022e286b"])
        data["files"][0]["body"] = "print(1)"
        errors = validate_source_index(data, registry)
        self.assertIn("index.files[0]: unknown field body", errors)

    def test_tracked_indexes_match_registry_counts_and_revisions(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        for snapshot_id, snapshot in registry.items():
            data = json.loads((ROOT / "research/indexes" / f"{snapshot_id}.json").read_text())
            self.assertEqual(data["snapshot"]["revision"], snapshot.revision)
            self.assertEqual(len(data["files"]), snapshot.materialized_file_count)
            self.assertEqual(validate_source_index(data, registry), [])

    def test_real_indexes_keep_duplicate_qualnames_but_unique_line_ids(self):
        expected_groups = {"mindspeed-mm-0edd553e": 10, "moss-tts-ad99ec5f": 1}
        for snapshot_id, expected in expected_groups.items():
            data = json.loads((ROOT / "research/indexes" / f"{snapshot_id}.json").read_text())
            pairs = collections.Counter((row["path"], row["qualname"]) for row in data["symbols"])
            self.assertEqual(sum(count > 1 for count in pairs.values()), expected)
            self.assertEqual(len({row["id"] for row in data["symbols"]}), len(data["symbols"]))
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

Expected: validator prints exactly `validated 4 source indexes: 3270 files; no absolute paths or source bodies`; all four `cmp` commands are silent and exit 0. On a machine without checkouts, skip only this reproduction block; fixture tests and validation of already committed outputs still run. The contract test also confirms the observed duplicate-qualname groups are exactly MM 10 and MOSS 1 while all line-bearing IDs are unique.

- [ ] **Step 6: 审计公开追踪边界**

Run:

```bash
git ls-files | rg '(^|/)\.superpowers/source-checkouts/|\.(safetensors|ckpt|pt|pth|onnx|gguf|wav|mp3|m4a|flac)$|(^|/)(weights|datasets|checkpoints)(/|$)' && exit 1 || true
rg -n '"(source_root|body|source|text|local_path)"\s*:' research/indexes
rg -n '/Users/|[A-Za-z]:\\\\' research/indexes
```

Expected: all three audits have no output; no source tree, asset, full source body, or absolute local path is tracked.

- [ ] **Step 7: 记录 acquisition/index identity boundary**

Append a dated `Phase 2 source-index foundation` entry to `IMPLEMENTATION_NOTES.md`: list all four snapshot IDs/acquisition kinds; preserve the Qwen two exact exclusions, MOSS 18 exact excluded paths and uninitialized `moss_audio_tokenizer@56776e867cb38446fa4bc00d0aceccab5001b008`; state that Git/archive identity is inherited from acquisition handoffs and not proved by the indexer, while `content_digest` covers only deterministic materialized index content. Record that both MindSpeed inputs are codeload archives and the observed duplicate-qualname counts are MM 10/MOSS 1.

- [ ] **Step 8: 运行 Python suite 并提交 indexes**

Run: `python3 -m unittest discover -s tests -p 'test_*.py' -v`

Expected: every discovered research and Phase 2/index test passes; report the runner's actual total.

```bash
git add scripts/validate_phase2.py tests/test_phase2_contracts.py research/indexes IMPLEMENTATION_NOTES.md
git commit -m "data: add reproducible selected source indexes"
```

Expected: one commit containing only validator/test/index outputs; no ignored tree is staged.

### Task 4: 建立 target evidence 与 no-silent-omission coverage contracts

**Files:**
- Create: `research/target-evidence.json`
- Create: `research/target-coverage.csv`
- Create: `research/schemas/target-evidence.schema.json`
- Create: `tests/fixtures/evidence/qwen3-tts-excerpts.json`
- Modify: `tests/test_phase2_contracts.py`
- Modify: `scripts/phase2_contracts.py`
- Modify: `scripts/validate_phase2.py`

**Interfaces:**
- Consumes: target source index `qwen3-tts-022e286b.json`, fixed target blob URL template, `research/source-ledger.csv`, official baseline and approved selection proposal.
- Produces: `validate_against_schema(data: object, schema: dict, path: str) -> list[str]`, `load_target_evidence_schema() -> dict`, `load_evidence(path: Path) -> dict[str, Evidence]`, `validate_evidence(data: object, registry, target_index, ledger_ids, root=ROOT) -> list[str]`, `validate_target_coverage(index, rows, evidence=None, page_catalog=None) -> list[str]`; when `evidence is None`, coverage validation loads `research/target-evidence.json`, so the two-argument test and explicit production call share one contract.

- [ ] **Step 1: 写入 evidence/coverage failing tests**

Append:

```python
import csv

from scripts.phase2_contracts import (load_evidence, load_snapshot_registry,
                                     validate_evidence, validate_target_coverage)


def registry():
    return load_snapshot_registry(ROOT / "research/source-snapshots.json")


def target_index():
    return json.loads((ROOT / "research/indexes/qwen3-tts-022e286b.json").read_text())


def ledger_ids():
    return {row["source_id"] for row in csv.DictReader((ROOT / "research/source-ledger.csv").open())}


def valid_evidence_document():
    def source_record(evidence_id, path):
        return {"evidence_id": evidence_id, "snapshot_id": "qwen3-tts-022e286b", "path": path,
            "start_line": 1, "end_line": 2, "state": "verified", "claim": "claim", "quote": "",
            "source_ids": ["SRC-001"], "decision_refs": []}
    return {"schema_version": 1, "records": [
        source_record("E-1", "pyproject.toml"), source_record("E-2", "LICENSE"),
        {"evidence_id": "E-3", "snapshot_id": None, "path": None, "start_line": None, "end_line": None,
         "state": "inference", "claim": "decision", "quote": "", "source_ids": ["SRC-019"],
         "decision_refs": ["research/reference-selection-proposal.md"]},
    ]}


class TargetCoverageTest(unittest.TestCase):
    def test_every_target_file_has_exactly_one_disposition(self):
        target = json.loads((ROOT / "research/indexes/qwen3-tts-022e286b.json").read_text())
        errors = validate_target_coverage(target, ROOT / "research/target-coverage.csv")
        self.assertEqual(errors, [])

    def test_evidence_has_four_states_and_bounded_quotes(self):
        evidence = load_evidence(ROOT / "research/target-evidence.json")
        self.assertEqual({row.state for row in evidence.values()}, {"verified", "project_claim", "inference", "pending_hardware"})
        self.assertTrue(all(len(row.quote) <= 240 and row.quote.count("\n") < 8 for row in evidence.values()))

    def test_evidence_ranges_exist_in_index_and_quotes_match_fixed_lines(self):
        target = json.loads((ROOT / "research/indexes/qwen3-tts-022e286b.json").read_text())
        excerpts = json.loads((ROOT / "tests/fixtures/evidence/qwen3-tts-excerpts.json").read_text())
        evidence = load_evidence(ROOT / "research/target-evidence.json")
        quoted = {evidence_id for evidence_id, row in evidence.items() if row.quote}
        self.assertEqual(quoted, set(excerpts))
        for evidence_id, lines in excerpts.items():
            row = evidence[evidence_id]
            self.assertTrue(row.quote)
            self.assertEqual(lines["path"], row.path)
            self.assertEqual([lines["start_line"], lines["end_line"]], [row.start_line, row.end_line])
            self.assertIn(row.quote, "\n".join(lines["lines"]))

    def test_all_source_ids_exist_in_phase1_ledger(self):
        ledger_ids = {row["source_id"] for row in csv.DictReader((ROOT / "research/source-ledger.csv").open())}
        for row in load_evidence(ROOT / "research/target-evidence.json").values():
            self.assertTrue(row.source_ids)
            self.assertLessEqual(set(row.source_ids), ledger_ids)

    def test_evidence_rejects_reversed_range_wrong_snapshot_and_bad_decision_ref(self):
        data = valid_evidence_document()
        data["records"][0].update({"start_line": 8, "end_line": 7})
        data["records"][1]["snapshot_id"] = "moss-tts-ad99ec5f"
        data["records"][2]["decision_refs"] = ["/tmp/decision.md"]
        errors = validate_evidence(data, registry(), target_index(), ledger_ids(), ROOT)
        self.assertIn("evidence.records[0]: start_line exceeds end_line", errors)
        self.assertIn("evidence.records[1].snapshot_id: expected target snapshot qwen3-tts-022e286b", errors)
        self.assertIn("evidence.records[2].decision_refs: disallowed /tmp/decision.md", errors)

    def test_evidence_schema_rejects_container_and_list_contracts(self):
        mutations = [
            (lambda row: row.update(source_ids=[]), "evidence.records[0].source_ids: fewer than 1 items"),
            (lambda row: row.update(source_ids=["SRC-001", "SRC-001"]), "evidence.records[0].source_ids: duplicate item"),
            (lambda row: row.update(quote="x" * 241), "evidence.records[0].quote: longer than 240"),
            (lambda row: row.update(start_line=None), "evidence.records[0]: expected exactly one oneOf branch"),
            (lambda row: row.update(extra=True), "evidence.records[0]: unknown field extra"),
            (lambda row: row.update(decision_refs=["research/reference-selection-proposal.md", "research/reference-selection-proposal.md"]), "evidence.records[0].decision_refs: duplicate item"),
        ]
        for mutate, expected in mutations:
            with self.subTest(expected=expected):
                data = valid_evidence_document()
                mutate(data["records"][0])
                self.assertIn(expected, validate_evidence(data, registry(), target_index(), ledger_ids(), ROOT))
```

- [ ] **Step 2: 运行 tests 并确认 evidence/coverage 缺失**

Run: `python3 -m unittest tests.test_phase2_contracts.TargetCoverageTest -v`

Expected: FAIL with `FileNotFoundError` for `research/target-coverage.csv` or `research/target-evidence.json`.

- [ ] **Step 3: 写入 fixed target evidence records**

Create `research/schemas/target-evidence.schema.json` and use it from the validator. Root keys are exactly `schema_version` and `records`; each record keys are exactly `evidence_id`, `snapshot_id`, `path`, `start_line`, `end_line`, `state`, `claim`, `quote`, `source_ids`, `decision_refs`. Require non-empty unique `source_ids` matching `^SRC-[0-9]{3}$`, a unique `decision_refs` array, four-state enum, claim length 1..500 and quote length <=240. Use `oneOf`: text-range records require string `snapshot_id/path` plus integer `start_line/end_line`; file-only records require string `snapshot_id/path` and null lines; ledger-only records require all four fields to be `null`. Create `research/target-evidence.json` with the following records; every text range must exist in the target index and satisfy `end_line <= file.line_count`, while file-only evidence is allowed only for an indexed binary and renders without a line anchor.

Use this exact schema shape (the shared validator explicitly supports every keyword present here):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object", "additionalProperties": false,
  "required": ["schema_version", "records"],
  "properties": {
    "schema_version": {"const": 1},
    "records": {"type": "array", "items": {
      "type": "object", "additionalProperties": false,
      "required": ["evidence_id", "snapshot_id", "path", "start_line", "end_line", "state", "claim", "quote", "source_ids", "decision_refs"],
      "properties": {
        "evidence_id": {"type": "string", "pattern": "^[A-Z0-9-]+$"},
        "snapshot_id": {"type": ["string", "null"]}, "path": {"type": ["string", "null"]},
        "start_line": {"type": ["integer", "null"], "minimum": 1},
        "end_line": {"type": ["integer", "null"], "minimum": 1},
        "state": {"enum": ["verified", "project_claim", "inference", "pending_hardware"]},
        "claim": {"type": "string", "minLength": 1, "maxLength": 500},
        "quote": {"type": "string", "maxLength": 240},
        "source_ids": {"type": "array", "minItems": 1, "uniqueItems": true, "items": {"type": "string", "pattern": "^SRC-[0-9]{3}$"}},
        "decision_refs": {"type": "array", "uniqueItems": true, "items": {"type": "string", "minLength": 1}}
      },
      "oneOf": [
        {"properties": {"snapshot_id": {"type": "string"}, "path": {"type": "string"}, "start_line": {"type": "integer", "minimum": 1}, "end_line": {"type": "integer", "minimum": 1}}},
        {"properties": {"snapshot_id": {"type": "string"}, "path": {"type": "string"}, "start_line": {"type": "null"}, "end_line": {"type": "null"}}},
        {"properties": {"snapshot_id": {"type": "null"}, "path": {"type": "null"}, "start_line": {"type": "null"}, "end_line": {"type": "null"}}}
      ]
    }}
  }
}
```

Add schema regression cases for an empty/duplicate `source_ids`, invalid/duplicate `decision_refs`, overlong quote, mixed null/source range, and unknown nested field; each must return a stable validation error and not crash.

| Evidence ID | Path and fixed lines | State | Source IDs | Claim used by pages |
| --- | --- | --- | --- | --- |
| `TGT-SCOPE-001` | `finetuning/README.md:3-10` | `verified` | `SRC-001` | public recipe is 12Hz Base single-speaker SFT; advanced/multi-speaker work is not public here |
| `TGT-SCOPE-002` | ledger-only | `project_claim` | `SRC-001, SRC-003, SRC-004, SRC-005` | official report/collections describe the released family and claims; inventories do not prove a fixed public 25Hz checkpoint |
| `TGT-PKG-001` | `pyproject.toml:1-45` | `verified` | `SRC-001` | package metadata, Python floor and runtime dependencies |
| `TGT-PKG-002` | `qwen_tts/core/__init__.py:16-19` | `verified` | `SRC-001` | package exports both 12Hz and 25Hz tokenizer config/model classes |
| `TGT-PKG-003` | `LICENSE:1-201` | `verified` | `SRC-001` | official target source root carries Apache License 2.0 text; weights/data remain separately scoped |
| `TGT-PKG-004` | `MANIFEST.in:1-13` | `verified` | `SRC-001` | source distribution includes package data but explicitly prunes assets, examples and finetuning |
| `TGT-PKG-005` | `qwen_tts/__init__.py:17-24` | `verified` | `SRC-001` | root package imports model/tokenizer wrappers while `__all__` only names version |
| `TGT-PKG-006` | `qwen_tts/__main__.py:16-24` | `verified` | `SRC-001` | module entry prints the package CLI entrypoint hint |
| `TGT-API-001` | `qwen_tts/inference/qwen3_tts_model.py:83-121` | `verified` | `SRC-001` | `from_pretrained` registers AutoConfig/AutoModel/AutoProcessor then loads model and processor |
| `TGT-API-002` | `qwen_tts/inference/qwen3_tts_model.py:356-633` | `verified` | `SRC-001` | Base voice clone prompt and generation API |
| `TGT-API-003` | `qwen_tts/inference/qwen3_tts_model.py:637-839` | `verified` | `SRC-001` | VoiceDesign and CustomVoice public wrapper APIs |
| `TGT-CLI-001` | `qwen_tts/cli/demo.py:91-108` | `verified` | `SRC-001` | target CLI defaults are `cuda:0`, BF16 and FlashAttention-2 |
| `TGT-CLI-002` | `qwen_tts/cli/demo.py:605-613` | `verified` | `SRC-001` | parsed target CLI values flow into `from_pretrained` |
| `TGT-CONFIG-001` | `qwen_tts/core/models/configuration_qwen3_tts.py:22-499` | `verified` | `SRC-001` | speaker, code predictor, Talker and composite config nesting |
| `TGT-MODEL-001` | `qwen_tts/core/models/modeling_qwen3_tts.py:311-393` | `verified` | `SRC-001` | ECAPA-style speaker encoder produces the speaker embedding |
| `TGT-MODEL-002` | `qwen_tts/core/models/modeling_qwen3_tts.py:1427-1810` | `verified` | `SRC-001` | Talker backbone, codec-0 LM head and residual code predictor integration |
| `TGT-MODEL-003` | `qwen_tts/core/models/modeling_qwen3_tts.py:1813-2292` | `verified` | `SRC-001` | composite conditional generation and prompt/speaker injection flow |
| `TGT-MODEL-004` | `qwen_tts/core/models/modeling_qwen3_tts.py:1612-1633` | `verified` | `SRC-001` | `forward_sub_talker_finetune` returns residual-codebook loss |
| `TGT-MODEL-005` | `qwen_tts/core/models/modeling_qwen3_tts.py:526-559` | `verified` | `SRC-001` | Talker RoPE math disables autocast and computes in FP32 before restoring input dtype |
| `TGT-MODEL-006` | `qwen_tts/core/models/modeling_qwen3_tts.py:595-610` | `verified` | `SRC-001` | RMSNorm variance is computed in FP32 |
| `TGT-MODEL-007` | `qwen_tts/core/models/modeling_qwen3_tts.py:634-657` | `verified` | `SRC-001` | eager attention softmax uses FP32 then casts to query dtype |
| `TGT-TOK12-001` | `qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py:780-1024` | `verified` | `SRC-001` | split RVQ, 12Hz model encode/decode and causal/chunked decoder |
| `TGT-TOK12-002` | `qwen_tts/core/tokenizer_12hz/configuration_qwen3_tts_tokenizer_v2.py:137-169` | `verified` | `SRC-001` | defaults are 24kHz, 1920 sample stride and 16 valid quantizers |
| `TGT-TOK12-003` | `qwen_tts/core/tokenizer_12hz/configuration_qwen3_tts_tokenizer_v2.py:147-169` | `inference` | `SRC-001` | `24000/1920 = 12.5` frames/s is arithmetic derived from verified defaults, distinct from the “12Hz” name |
| `TGT-TOK25-001` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:996-1273` | `verified` | `SRC-001` | DiT mel sampling and BigVGAN waveform decoder code exists |
| `TGT-TOK25-002` | ledger-only | `pending_hardware` | `SRC-001, SRC-003, SRC-004, SRC-005` | official source/report/collections do not establish a fixed public executable 25Hz checkpoint |
| `TGT-TOK25-003` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:1426-1440` | `verified` | `SRC-001` | `from_pretrained` resolves `campplus.onnx` and loads it |
| `TGT-TOK25-004` | `qwen_tts/core/tokenizer_25hz/vq/speech_vq.py:16-32` | `verified` | `SRC-001` | speech VQ directly imports SoX, ONNX Runtime, Kaldi compliance and VQ/Whisper modules |
| `TGT-TOK25-005` | `qwen_tts/core/tokenizer_25hz/vq/speech_vq.py:118-150` | `verified` | `SRC-001` | x-vector extraction uses ONNX CPUExecutionProvider plus SoX normalization and Kaldi fbank |
| `TGT-TOK25-006` | `qwen_tts/core/tokenizer_25hz/vq/whisper_encoder.py:29-36` | `verified` | `SRC-001` | flash-attn import has a manual PyTorch fallback |
| `TGT-TOK25-007` | `qwen_tts/core/tokenizer_25hz/vq/whisper_encoder.py:161-191` | `verified` | `SRC-001` | attention falls back manually when flash-attn is absent or dtype is not FP16/BF16 |
| `TGT-TOK25-008` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:1235-1253` | `verified` | `SRC-001` | FP32 decoder overrides FA2/eager with SDPA fallback |
| `TGT-TOK25-009` | `qwen_tts/core/tokenizer_25hz/vq/core_vq.py:113-231` | `verified` | `SRC-001` | direct Euclidean codebook quantize/dequantize implementation |
| `TGT-TOK25-010` | `qwen_tts/core/tokenizer_25hz/vq/core_vq.py:334-521` | `verified` | `SRC-001` | residual/group residual VQ encode/decode implementation |
| `TGT-TOK25-011` | `qwen_tts/core/models/modeling_qwen3_tts.py:1891-1936` | `verified` | `SRC-001` | main model loads `speech_tokenizer/*`, tokenizer config and `generation_config.json` |
| `TGT-TOK25-012` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:1282-1394` | `verified` | `SRC-001` | encoder plus composite tokenizer wiring and rate accessors exist |
| `TGT-TOK25-013` | `qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py:1444-1526` | `verified` | `SRC-001` | composite encode/decode calls encoder, VQ decoder and waveform decoder |
| `TGT-TOK25-014` | file-only `qwen_tts/core/tokenizer_25hz/vq/assets/mel_filters.npz` | `verified` | `SRC-001` | target index directly records this bundled asset's path/bytes/SHA-256 and `kind=binary`; no line claim is made |
| `TGT-PROC-001` | `qwen_tts/core/models/processing_qwen3_tts.py:27-103` | `verified` | `SRC-001` | processor wraps Qwen tokenizer/ChatML text behavior |
| `TGT-PROC-002` | `qwen_tts/inference/qwen3_tts_tokenizer.py:44-410` | `verified` | `SRC-001` | 12Hz/25Hz audio wrapper normalizes, encodes, decodes and exposes sample-rate contracts |
| `TGT-DATA-001` | `finetuning/prepare_data.py:24-68` | `verified` | `SRC-001` | preprocessing materializes `audio_codes` into JSONL |
| `TGT-DATA-003` | `finetuning/prepare_data.py:24-35` | `verified` | `SRC-001` | preprocessing defaults to `cuda:0` and passes it as tokenizer `device_map` |
| `TGT-DATA-002` | `finetuning/dataset.py:33-217` | `verified` | `SRC-001` | dataset makes ChatML text, 24kHz reference mel and dual-track collate tensors |
| `TGT-TRAIN-000` | `finetuning/sft_12hz.py:44-52` | `verified` | `SRC-001` | SFT initializes BF16 Accelerate and loads BF16 model with FlashAttention-2 |
| `TGT-TRAIN-001` | `finetuning/sft_12hz.py:62-64` | `verified` | `SRC-001` | code passes model, optimizer and DataLoader to `accelerator.prepare` |
| `TGT-TRAIN-002` | `finetuning/sft_12hz.py:82-111` | `verified` | `SRC-001` | code accesses speaker encoder, Talker internals and custom method through variable `model`; `TGT-TRAIN-001` separately proves `model` is returned by `accelerator.prepare` |
| `TGT-TRAIN-003` | `finetuning/sft_12hz.py:30-30` | `inference` | `SRC-001` | module global implies per-interpreter state; actual per-process behavior depends on launch/runtime |
| `TGT-TRAIN-004` | `finetuning/sft_12hz.py:83-84` | `inference` | `SRC-001` | under multi-process launch each process may retain the first embedding it sees; execution is pending |
| `TGT-TRAIN-005` | `finetuning/sft_12hz.py:100-121` | `verified` | `SRC-001` | exact loss is `outputs.loss + 0.3 * sub_talker_loss`, then backward, clip and optimizer step |
| `TGT-TRAIN-006` | `finetuning/sft_12hz.py:58-64` | `inference` | `SRC-001` | DataLoader sharding is delegated to Accelerate runtime after `prepare`; exact wrapper/version behavior is pending execution |
| `TGT-TRAIN-007` | `finetuning/sft_12hz.py:82-111` | `inference` | `SRC-001` | direct access to custom attributes/methods through the prepared model is wrapper/version-sensitive and pending multi-process execution |
| `TGT-EXPORT-001` | `finetuning/sft_12hz.py:126-158` | `verified` | `SRC-001` | per-epoch copy/config mutation, speaker row 3000 and safetensors export |
| `TGT-EXPORT-002` | `finetuning/sft_12hz.py:35-35` | `verified` | `SRC-001` | default initialization value is a Hugging Face repo ID |
| `TGT-EXPORT-003` | `finetuning/sft_12hz.py:126-132` | `inference` | `SRC-001` | export uses `copytree` and directly opens `MODEL_PATH/config.json`, so actual export statically requires a local directory despite the default repo ID |
| `TGT-GAP-001` | `finetuning/sft_12hz.py:31-158` | `inference` | `SRC-001` | absence of scheduler/resume/validation in this file is a fixed-tree audit inference, not proof of global absence |
| `TGT-HW-001` | `pyproject.toml:1-45` | `pending_hardware` | `SRC-001` | no CANN/torch-npu dependency or CANN 8.5.2 compatibility evidence exists in the official target package |
| `PH1-ROLE-MM` | ledger-only | `inference` | `SRC-019, SRC-020, SRC-021, SRC-022, SRC-043` | approved selection makes exact 12Hz NPU SFT the main reference role |
| `PH1-ROLE-LLM` | ledger-only | `inference` | `SRC-026, SRC-027, SRC-079, SRC-083` | approved selection limits MindSpeed-LLM to text scaling satellite evidence |
| `PH1-ROLE-MOSS` | ledger-only | `inference` | `SRC-030, SRC-031, SRC-047, SRC-103` | approved selection limits MOSS to speech/codec contrast |
| `PH1-ENV-LANES` | ledger-only | `pending_hardware` | `SRC-028, SRC-071, SRC-087` | native 8.5.0 learning lane and user 8.5.2 validation lane remain distinct; 8.5.2 compatibility is unknown |

Use the explicit Source IDs column verbatim; do not infer a default while parsing the table. Set `decision_refs: []` on every `TGT-*` record. Set `PH1-ROLE-MM`, `PH1-ROLE-LLM`, and `PH1-ROLE-MOSS` to `decision_refs: ["research/reference-selection-proposal.md", "research/selected-revisions.csv"]`; set `PH1-ENV-LANES` to `decision_refs: ["research/reference-selection-proposal.md"]`. These internal references identify the approved selection decision, while `source_ids` continue to support external capability/compatibility facts. Non-empty quotes are only `single-speaker fine-tuning`, `AutoModel.from_pretrained`, `outputs.loss + 0.3 * sub_talker_loss`, and `checkpoint-epoch-{epoch}`. Put those four exact line slices and line numbers in `tests/fixtures/evidence/qwen3-tts-excerpts.json`; the test above proves the set of non-empty quote IDs equals the fixture keys and every quote occurs inside its declared range. All other quotes are empty. Generate fixed URLs from the registry template only for text files/ranges; binary file links use the fixed blob path without `#L` anchors, ledger-only records link their `source_ids` through `source-ledger.csv`, and the renderer displays each `decision_refs` path as an internal decision link.

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
LICENSE,mapped,index.html,public-scope,TGT-PKG-003,
MANIFEST.in,mapped,target/package-inference-api.html,package-layout,TGT-PKG-004,
README.md,mapped,index.html,public-scope,TGT-SCOPE-002,
examples/test_model_12hz_base.py,mapped,target/package-inference-api.html,base-api,TGT-API-002,
examples/test_model_12hz_custom_voice.py,mapped,target/package-inference-api.html,custom-api,TGT-API-003,
examples/test_model_12hz_voice_design.py,mapped,target/package-inference-api.html,voice-design-api,TGT-API-003,
examples/test_tokenizer_12hz.py,mapped,target/tokenizer-12hz.html,encode-contract,TGT-TOK12-001,
finetuning/README.md,mapped,target/sft-data-collate.html,public-recipe,TGT-SCOPE-001,
finetuning/dataset.py,mapped,target/sft-data-collate.html,collate-contract,TGT-DATA-002,
finetuning/prepare_data.py,mapped,target/sft-data-collate.html,offline-codes,TGT-DATA-001,
finetuning/sft_12hz.py,mapped,target/sft-training-loop.html,training-loop,TGT-TRAIN-005,
pyproject.toml,mapped,target/package-inference-api.html,package-layout,TGT-PKG-001,
qwen_tts/__init__.py,mapped,target/package-inference-api.html,package-layout,TGT-PKG-005,
qwen_tts/__main__.py,mapped,target/package-inference-api.html,package-layout,TGT-PKG-006,
qwen_tts/cli/demo.py,mapped,target/package-inference-api.html,target-defaults,TGT-CLI-001|TGT-CLI-002,
qwen_tts/core/__init__.py,mapped,target/tokenizer-12hz.html,package-tokenizer-registry,TGT-PKG-002,
qwen_tts/core/models/__init__.py,mapped,target/model-architecture.html,composite-config,TGT-CONFIG-001,
qwen_tts/core/models/configuration_qwen3_tts.py,mapped,target/model-architecture.html,composite-config,TGT-CONFIG-001,
qwen_tts/core/models/modeling_qwen3_tts.py,mapped,target/model-architecture.html,talker,TGT-MODEL-002,
qwen_tts/core/models/processing_qwen3_tts.py,mapped,target/processor-contracts.html,text-contract,TGT-PROC-001,
qwen_tts/core/tokenizer_12hz/configuration_qwen3_tts_tokenizer_v2.py,mapped,target/tokenizer-12hz.html,configuration,TGT-TOK12-002|TGT-TOK12-003,
qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py,mapped,target/tokenizer-12hz.html,encode-contract,TGT-TOK12-001,
qwen_tts/core/tokenizer_25hz/configuration_qwen3_tts_tokenizer_v1.py,pending,target/tokenizer-25hz.html,asset-inventory,TGT-TOK25-002,25Hz public checkpoint and executable path remain unknown
qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py,pending,target/tokenizer-25hz.html,dit-bigvgan,TGT-TOK25-001,Static dependencies and encode/decode wiring are verified but runtime assets and execution are unverified
qwen_tts/core/tokenizer_25hz/vq/assets/mel_filters.npz,pending,target/tokenizer-25hz.html,bundled-filter,TGT-TOK25-014,Fixed binary URL and metadata only; binary body is never copied and execution remains unverified
qwen_tts/core/tokenizer_25hz/vq/core_vq.py,pending,target/tokenizer-25hz.html,vq-core,TGT-TOK25-009|TGT-TOK25-010,Direct VQ source is mapped; execution remains unverified
qwen_tts/core/tokenizer_25hz/vq/speech_vq.py,pending,target/tokenizer-25hz.html,speech-vq,TGT-TOK25-004|TGT-TOK25-005,Direct ONNX/SoX/Kaldi dependencies are mapped; execution remains unverified
qwen_tts/core/tokenizer_25hz/vq/whisper_encoder.py,pending,target/tokenizer-25hz.html,whisper-encoder,TGT-TOK25-006|TGT-TOK25-007,Direct flash-attn dtype/manual fallback is mapped; execution remains unverified
qwen_tts/inference/qwen3_tts_model.py,mapped,target/package-inference-api.html,load-chain,TGT-API-001,
qwen_tts/inference/qwen3_tts_tokenizer.py,mapped,target/processor-contracts.html,audio-wrapper,TGT-PROC-002,
```

- [ ] **Step 5: 实现 evidence and coverage validators**

Add frozen `Evidence` with the exact fields below. `validate_evidence` first calls the same total recursive schema validator, then parses unique IDs, validates every `source_id` against the CSV ledger, validates internal decision refs, and for source-backed records looks up `path` in the target index, rejects binary line ranges, and enforces `1 <= start_line <= end_line <= line_count`. The fixed test validates all non-empty quotes against exact range fixtures. `fixed_url(row, registry)` appends `#Lstart-Lend` only for source-backed text; binary coverage URLs are `<blob-template before #L>{path}` without a line anchor. `validate_target_coverage` uses `csv.DictReader`, compares its path multiset to target-index files, rejects unknown evidence IDs/dispositions, and requires reason/page/section according to disposition.

```python
DECISION_REFS = {
    "research/reference-selection-proposal.md",
    "research/selected-revisions.csv",
}


def validate_against_schema(data: object, schema: dict[str, object], path: str) -> list[str]:
    errors: list[str] = []
    _validate(data, schema, path, errors)
    return errors


@lru_cache(maxsize=1)
def load_target_evidence_schema() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "research/schemas/target-evidence.schema.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    snapshot_id: str | None
    path: str | None
    start_line: int | None
    end_line: int | None
    state: str
    claim: str
    quote: str
    source_ids: tuple[str, ...]
    decision_refs: tuple[str, ...]


EVIDENCE_STATES = {"verified", "project_claim", "inference", "pending_hardware"}
DISPOSITIONS = {"mapped", "excluded", "pending"}
```

`load_evidence()` runs `validate_evidence` with the production registry/index/ledger/root inputs, raises `ValueError` with the stable joined errors, and constructs `Evidence` by converting both `source_ids` and `decision_refs` JSON arrays to tuples; no alternate loader shape is permitted.

The core validator loop is mandatory and uses the target index rather than trusting evidence JSON:

```python
def validate_evidence(data, registry, target_index, ledger_ids, root=ROOT):
    errors = validate_against_schema(data, load_target_evidence_schema(), "evidence")
    if errors:
        return errors
    files = {row["path"]: row for row in target_index["files"]}
    seen = set()
    for i, row in enumerate(data["records"]):
        prefix = f"evidence.records[{i}]"
        if row["evidence_id"] in seen:
            errors.append(f"{prefix}.evidence_id: duplicate {row['evidence_id']}")
        seen.add(row["evidence_id"])
        for source_id in row["source_ids"]:
            if source_id not in ledger_ids:
                errors.append(f"{prefix}.source_ids: unknown {source_id}")
        for decision_ref in row["decision_refs"]:
            if decision_ref not in DECISION_REFS:
                errors.append(f"{prefix}.decision_refs: disallowed {decision_ref}")
            elif not (root / decision_ref).is_file():
                errors.append(f"{prefix}.decision_refs: missing {decision_ref}")
        if row["path"] is not None:
            file_row = files.get(row["path"])
            if file_row is None:
                errors.append(f"{prefix}.path: not in target index")
            elif row["start_line"] is None and file_row["kind"] != "binary":
                errors.append(f"{prefix}.path: file-only evidence requires indexed binary")
            elif row["start_line"] is not None and file_row["line_count"] is None:
                errors.append(f"{prefix}.path: binary file cannot have line range")
            elif row["end_line"] is not None and row["end_line"] > file_row["line_count"]:
                errors.append(f"{prefix}.end_line: exceeds {row['path']} line_count")
            if row["start_line"] is not None and row["start_line"] > row["end_line"]:
                errors.append(f"{prefix}: start_line exceeds end_line")
            target_snapshot = target_index["snapshot"]["snapshot_id"]
            if row["snapshot_id"] != target_snapshot:
                errors.append(f"{prefix}.snapshot_id: expected target snapshot {target_snapshot}")
    return errors
```

Use one coverage signature everywhere:

```python
def validate_target_coverage(index, rows, evidence=None, page_catalog=None):
    if evidence is None:
        evidence = load_evidence(ROOT / "research/target-evidence.json")
    csv_rows = list(csv.DictReader(rows.open(encoding="utf-8"))) if isinstance(rows, Path) else list(rows)
    errors: list[str] = []
    expected = collections.Counter(row["path"] for row in index["files"])
    actual = collections.Counter(row.get("path", "") for row in csv_rows)
    for path in sorted((expected - actual).elements()):
        errors.append(f"target coverage: missing {path}")
    for path in sorted((actual - expected).elements()):
        errors.append(f"target coverage: unexpected or duplicate {path}")
    known = set(evidence)
    catalog = None if page_catalog is None else {
        page["slug"]: {section["id"] for section in page["sections"]}
        for page in page_catalog
    }
    for index_number, row in enumerate(csv_rows):
        prefix = f"coverage[{index_number}] {row.get('path', '')}"
        disposition = row.get("disposition", "")
        if disposition not in DISPOSITIONS:
            errors.append(f"{prefix}: invalid disposition {disposition}")
        if disposition in {"mapped", "pending"} and (not row.get("page") or not row.get("section")):
            errors.append(f"{prefix}: page and section required")
        if disposition in {"excluded", "pending"} and not row.get("reason"):
            errors.append(f"{prefix}: reason required")
        for evidence_id in filter(None, row.get("evidence_ids", "").split("|")):
            if evidence_id not in known:
                errors.append(f"{prefix}: unknown evidence {evidence_id}")
        if catalog is not None and disposition in {"mapped", "pending"}:
            if row["page"] not in catalog or row["section"] not in catalog[row["page"]]:
                errors.append(f"{prefix}: missing section {row['page']}#{row['section']}")
    return errors
```

Tests call both the two-argument default and the explicit `evidence=` form and assert identical error lists.

Extend `validate_phase2.py` default mode to run `validate_indexes()`, evidence validation and coverage validation; keep `--indexes-only` behavior unchanged.

- [ ] **Step 6: 运行 contract and full validation**

Run:

```bash
python3 -m unittest tests.test_phase2_contracts -v
python3 scripts/validate_phase2.py
```

Expected: every Phase 2 contract test passes. CLI sets `evidence_count = len(load_evidence(...))`, prints that value in `validated Phase 2 data: 4 indexes, {evidence_count} evidence records, 35 target coverage rows, 0 omissions`, and the test parses the printed integer and compares it to the loaded length rather than a hand-maintained literal.

- [ ] **Step 7: 提交 target evidence contracts**

```bash
git add research/target-evidence.json research/target-coverage.csv research/schemas/target-evidence.schema.json tests/fixtures/evidence/qwen3-tts-excerpts.json scripts/phase2_contracts.py scripts/validate_phase2.py tests/test_phase2_contracts.py
git commit -m "data: map target evidence and coverage"
```

Expected: one commit; no HTML or candidate source tree is changed yet.

### Task 5: 构建共享静态页面生成器、首页、索引与本地搜索

**Files:**
- Create: `content/site-foundation.json`
- Create: `research/schemas/page-catalog.schema.json`
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
- Produces: `validate_catalogs(data: object, evidence_ids: set[str]) -> list[str]`, `load_page_catalogs(paths: list[Path]) -> list[dict]`, `relative_href(from_slug: str, to_slug: str) -> str`, `decision_href(from_slug: str, decision_ref: str) -> str`, `render_page(page, navigation, evidence, search_documents) -> str`, `build_site(output_root: Path, catalog_paths: list[Path]) -> list[Path]`; four foundation pages plus local `search-index.json` in this task.

- [ ] **Step 1: 写入生成器 failing tests**

Create `tests/test_site_builder.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase2_contracts import Evidence
from scripts.site_builder import (build_search_documents, build_site, decision_href,
                                  load_page_catalogs, relative_href, render_page,
                                  script_safe_json, validate_catalogs)

ROOT = Path(__file__).resolve().parents[1]


def minimal_catalog(block=None, text="x"):
    block = block or {"type": "paragraph", "text": text, "state": "verified", "evidence_ids": ["E-1"]}
    return {"schema_version": 1, "pages": [{"slug": "index.html", "title": "Title", "summary": "Summary",
        "order": 1, "group": "foundation", "objectives": ["Learn"], "prerequisites": ["PyTorch"],
        "sections": [{"id": "intro", "title": "Intro", "blocks": [block]}]}]}


def fixture_indexes():
    return {"snap": {"files": [{"path": "pkg/a.py"}],
        "symbols": [{"id": "pkg/a.py:C:1", "path": "pkg/a.py", "qualname": "C"}], "configs": []}}


def fixture_evidence(decision_refs=()):
    return {"E-1": Evidence("E-1", None, None, None, None, "verified", "claim", "", ("SRC-001",), decision_refs)}


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

    def test_every_page_search_form_targets_relative_search_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            self.assertIn('action="search.html"', (output / "index.html").read_text())
            self.assertIn('action="../search.html"', (output / "indexes/source-files.html").read_text())

    def test_catalog_validator_rejects_unknown_evidence_and_block_field(self):
        data = minimal_catalog(block={"type": "paragraph", "text": "x", "state": "verified",
                                      "evidence_ids": ["MISSING"], "raw_html": "<b>x</b>"})
        errors = validate_catalogs(data, set())
        self.assertIn("catalog.pages[0].sections[0].blocks[0]: unknown field raw_html", errors)
        data = minimal_catalog(block={"type": "paragraph", "text": "x", "state": "verified",
                                      "evidence_ids": ["MISSING"]})
        errors = validate_catalogs(data, set())
        self.assertIn("catalog.pages[0]#intro: unknown evidence MISSING", errors)

    def test_relative_href_and_search_anchor_contract(self):
        self.assertEqual(relative_href("target/model.html", "search.html"), "../search.html")
        self.assertEqual(decision_href("index.html", "research/reference-selection-proposal.md"), "../research/reference-selection-proposal.md")
        self.assertEqual(decision_href("target/model.html", "research/reference-selection-proposal.md"), "../../research/reference-selection-proposal.md")
        documents = build_search_documents(minimal_catalog()["pages"], fixture_indexes())
        self.assertEqual(documents, sorted(documents, key=lambda row: (row["kind"], row["title"], row["href"])))
        symbol = next(row for row in documents if row["kind"] == "symbol")
        self.assertRegex(symbol["href"], r"^indexes/symbols-configs\.html#entry-[0-9a-f]{16}$")

    def test_render_resolves_evidence_decisions_and_escapes_all_values(self):
        page = minimal_catalog(text='<img src=x onerror="boom">')["pages"][0]
        html = render_page(page, [page], fixture_evidence(decision_refs=("research/reference-selection-proposal.md",)), [])
        self.assertIn('id="chapter-nav"', html)
        self.assertIn('id="article-content"', html)
        self.assertIn('id="evidence-rail"', html)
        self.assertIn('href="../research/reference-selection-proposal.md"', html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;img", html)
```

- [ ] **Step 2: 运行 tests 并确认 builder 缺失**

Run: `python3 -m unittest tests.test_site_builder -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.site_builder'`.

- [ ] **Step 3: 写入 foundation catalog**

Create `content/site-foundation.json` with `schema_version: 1` and exactly these four pages and sections:

| Order / slug | Title | Required sections and exact teaching contract |
| --- | --- | --- |
| `1 / index.html` | `Qwen3-TTS 官方目标源码学习路径` | `public-scope` [`TGT-SCOPE-002,TGT-PKG-003`]: static reading/license boundary only, no training/compatibility claim; `learning-path`: PyTorch single-card → package/API → model → tokenizers → contracts → SFT; `environment-lanes` [`PH1-ENV-LANES,TGT-HW-001`]: project-native `2.7.1 + 8.5.0` and target `2.7.1 + 8.5.2 unknown`; `phase-boundary`: list all five deferred work packages |
| `11 / indexes/source-files.html` | `四个固定快照文件索引` | `snapshot-provenance`: label Git sparse vs codeload archive correctly; `file-filters`: snapshot/kind/path; `future-interface`: main/scale/speech later pages consume path+hash+fixed link |
| `12 / indexes/symbols-configs.html` | `符号与配置项索引` | `symbol-index`: qualname/kind/path/line; `config-index`: key/owner/kind/path/line with no values; `limits`: AST/static-key index is not a runtime call graph |
| `13 / search.html` | `全站搜索` | `search-results`: inline JSON-driven results; `no-script-index`: initial HTML contains alphabetic links for all pages; `search-scope`: page title/summary/headings plus file/symbol/config metadata, never full source bodies |

The homepage must include the literal sentences `本阶段没有运行 Qwen3-TTS 训练。` and `CANN 8.5.2 兼容性：unknown，待真机验证。`. Every page has at least one objective, prerequisite `熟悉 PyTorch 单卡张量与训练循环`, and a four-state legend.

Create `research/schemas/page-catalog.schema.json` from this exact contract and load it through `load_page_catalog_schema()`: the catalog root is exactly `{schema_version: 1, pages: Page[]}`. A `Page` requires only `slug,title,summary,order,group,objectives,prerequisites,sections`; slug matches `^(index|search|indexes/[a-z0-9-]+|target/[a-z0-9-]+)\.html$`, order is positive integer, objectives/prerequisites are non-empty string arrays. A `Section` requires only `id,title,blocks`; id matches `^[a-z][a-z0-9-]*$`. Blocks use a `oneOf` tagged union with `additionalProperties:false`: `paragraph` requires only `type,text,state,evidence_ids`; `call_chain` requires only `type,items` where each item requires only `{label,path,symbol,evidence_ids}`; `table` requires only `type,headers,rows`; `source_refs` requires only `type,evidence_ids`; `index_table` requires only `type,dataset` with enum `files|symbols|configs`. Raw HTML is rejected. `validate_catalogs` also requires unique slugs/orders/section IDs, exact table row widths, and verifies every block evidence ID exists.

Implement the helper contracts without alternate field names:

```python
from __future__ import annotations

import hashlib
import html
import json
import posixpath
from functools import lru_cache
from pathlib import Path

from scripts.phase2_contracts import (DECISION_REFS, Evidence, load_evidence,
                                      load_snapshot_registry, validate_against_schema)

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_page_catalog_schema() -> dict[str, object]:
    return json.loads((ROOT / "research/schemas/page-catalog.schema.json").read_text(encoding="utf-8"))


def validate_catalogs(data: object, evidence_ids: set[str]) -> list[str]:
    errors = validate_against_schema(data, load_page_catalog_schema(), "catalog")
    if errors:
        return errors
    seen_slugs, seen_orders = set(), set()
    for page_index, page in enumerate(data["pages"]):
        prefix = f"catalog.pages[{page_index}]"
        if page["slug"] in seen_slugs: errors.append(f"{prefix}.slug: duplicate {page['slug']}")
        if page["order"] in seen_orders: errors.append(f"{prefix}.order: duplicate {page['order']}")
        seen_slugs.add(page["slug"]); seen_orders.add(page["order"])
        section_ids = [section["id"] for section in page["sections"]]
        if len(section_ids) != len(set(section_ids)): errors.append(f"{prefix}.sections: duplicate id")
        for section in page["sections"]:
            for block in section["blocks"]:
                if block["type"] == "table":
                    for row in block["rows"]:
                        if len(row) != len(block["headers"]):
                            errors.append(f"{prefix}#{section['id']}: row width {len(row)} expected {len(block['headers'])}")
                references = list(block.get("evidence_ids", []))
                references.extend(eid for item in block.get("items", []) for eid in item.get("evidence_ids", []))
                for evidence_id in references:
                    if evidence_id not in evidence_ids:
                        errors.append(f"{prefix}#{section['id']}: unknown evidence {evidence_id}")
    return errors


def load_page_catalogs(paths: list[Path]) -> list[dict[str, object]]:
    evidence = load_all_evidence()
    pages = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_catalogs(data, set(evidence))
        if errors: raise ValueError("\n".join(f"{path.as_posix()}: {error}" for error in errors))
        pages.extend(data["pages"])
    combined = {"schema_version": 1, "pages": pages}
    errors = validate_catalogs(combined, set(evidence))
    if errors: raise ValueError("\n".join(errors))
    return sorted(pages, key=lambda page: page["order"])


def relative_href(from_slug: str, to_slug: str) -> str:
    return posixpath.relpath(to_slug, posixpath.dirname(from_slug) or ".")


def decision_href(from_slug: str, decision_ref: str) -> str:
    if decision_ref not in DECISION_REFS:
        raise ValueError(f"disallowed decision ref {decision_ref}")
    return relative_href(from_slug, f"../{decision_ref}")


def load_all_indexes(root: Path = ROOT) -> dict[str, dict[str, object]]:
    registry = load_snapshot_registry(root / "research/source-snapshots.json")
    return {snapshot_id: json.loads((root / "research/indexes" / f"{snapshot_id}.json").read_text())
            for snapshot_id in sorted(registry)}


def load_all_evidence(root: Path = ROOT) -> dict[str, Evidence]:
    return load_evidence(root / "research/target-evidence.json")


def _anchor(kind: str, snapshot_id: str, identity: str) -> str:
    raw = f"{kind}\0{snapshot_id}\0{identity}".encode()
    return f"entry-{hashlib.sha256(raw).hexdigest()[:16]}"


def build_search_documents(pages, indexes) -> list[dict[str, str]]:
    docs = []
    for page in pages:
        docs.append({"kind": "page", "title": page["title"], "summary": page["summary"],
            "headings": " ".join(section["title"] for section in page["sections"]),
            "href": page["slug"], "path": "", "qualname": "", "key": ""})
    destinations = {"files": "indexes/source-files.html", "symbols": "indexes/symbols-configs.html", "configs": "indexes/symbols-configs.html"}
    for snapshot_id, index in indexes.items():
        for kind in ("files", "symbols", "configs"):
            for row in index[kind]:
                identity = row["path"] if kind == "files" else row["id"]
                docs.append({"kind": kind[:-1], "title": identity, "summary": snapshot_id,
                    "headings": "", "href": f"{destinations[kind]}#{_anchor(kind, snapshot_id, identity)}",
                    "path": row.get("path", ""), "qualname": row.get("qualname", ""), "key": row.get("key", "")})
    for doc in docs:
        doc["searchable"] = " ".join(doc[key] for key in ("title", "summary", "headings", "path", "qualname", "key")).casefold()
    return sorted(docs, key=lambda doc: (doc["kind"], doc["title"], doc["href"]))
```

Index-table rendering must put `_anchor(...)` on the exact row that the search `href` targets.

- [ ] **Step 4: 实现 shared partial renderer and build CLI**

Create `scripts/site_builder.py` with HTML escaping on every catalog/index value. Reuse the existing DOM contracts exactly: `chapter-nav`, `article-content`, `evidence-rail`, `toggle-left`, `toggle-right`, `site-search`, `chapter-tree`, `page-toc`, evidence cards, drawer buttons and `assets/app.js`. Compute asset/search/nav links with `relative_href(from_slug, to_slug) = posixpath.relpath(to_slug, posixpath.dirname(from_slug) or ".")`; every page search form uses `method="get"`, input name `q`, and `action=relative_href(page["slug"], "search.html")`. Set `aria-current="page"`, generate one `h1`, and emit previous/next links from sorted `order` only when the neighbor exists in loaded catalogs. For index fixed links, text records use line anchors and binary records use the fixed blob URL without an anchor.

`render_page(page, navigation, evidence, search_documents) -> str` follows this complete deterministic algorithm: (1) reject any block evidence ID absent from `evidence`; (2) compute CSS/JS/search/nav links with `relative_href`; (3) render the shared header/search form, `chapter-nav`, `chapter-tree`, `article-content`, one escaped `h1`, objectives/prerequisites, and `page-toc`; (4) dispatch only the five tagged block types, escape every scalar with `html.escape(..., quote=True)`, verify table row widths, and give index rows the same `_anchor` used by search; (5) collect referenced evidence in first-use order and render `evidence-rail` cards with state text, fixed source/ledger links, and each allowlisted internal decision path through `decision_href(page["slug"], ref)`—therefore `site/index.html` uses `../research/...` and `site/target/*.html` uses `../../research/...`; (6) render `toggle-left`/`toggle-right` controls and previous/next navigation; (7) on `search.html`, embed `script_safe_json(search_documents)` in `#search-data` and render the alphabetical no-script page directory; (8) join fixed partials with `\n` and end with exactly one newline. Stable failures are `page <slug>#<section>: unknown evidence <id>`, `block <type>: unsupported`, and `table <section>: row width <n> expected <m>`.

Dependency direction is one-way at module initialization: `site_builder.py` imports data contracts/loaders from `phase2_contracts.py`; `phase2_contracts.py` never imports `site_builder.py` at module import time. Task 8 uses function-local imports for both `load_all_indexes` in `validate_cross_contracts` and `build_site` in the fresh-build validator only after both modules are initialized, preventing a circular import.

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

`search.html` embeds the same documents as `site/assets/search-index.json`; runtime does not fetch search JSON or any remote resource. Supported offline use is local HTTP plus browser offline mode; no `file://` promise is made. Preserve an initial-HTML alphabetical page directory under `no-script-index` so content remains navigable when JavaScript is disabled.

Extend the existing `SearchController` constructor with `windowRef = window`, store `this.window`, `this.data`, `this.results`, and `this.resultsStatus`, then initialize query state before registering later interactions. This closes the direct-link contract used by Playwright:

```javascript
const query = new URLSearchParams(this.window.location.search).get('q') ?? '';
if (this.input) this.input.value = query;
this.renderResults(query);
this.form?.addEventListener('submit', (event) => {
  if (!this.data || this.window.location.pathname.split('/').pop() !== 'search.html') return;
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

Expected: all foundation tests pass; CLI prints counts derived from `len(pages)`/`len(documents)`; the four HTML files and search JSON are deterministic; malicious `</script>` input is encoded as `\u003c/script`; root and nested forms have the correct relative search action.

- [ ] **Step 8: 提交 generator foundation**

```bash
git add content/site-foundation.json research/schemas/page-catalog.schema.json scripts/site_builder.py scripts/build_site.py tests/test_site_builder.py site/index.html site/indexes site/search.html site/assets/app.js site/assets/theme.css site/assets/layout.css site/assets/search-index.json
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
| `2 / target/package-inference-api.html` | `package-layout` [`TGT-PKG-001,TGT-PKG-002,TGT-PKG-003,TGT-PKG-004,TGT-PKG-005,TGT-PKG-006`]: exports/CLI/dependencies/license and the source-distribution prune of assets/examples/finetuning; `target-defaults` [`TGT-CLI-001,TGT-CLI-002`]: CUDA:0/BF16/FA2 are target NVIDIA defaults, not migration advice; `load-chain` [`TGT-API-001`]: `Qwen3TTSModel.from_pretrained → AutoConfig.register → AutoModel.from_pretrained → AutoProcessor.from_pretrained`; `base-api` [`TGT-API-002`]: prompt → voice clone; `voice-design-api` and `custom-api` [`TGT-API-003`]; `package-boundary`: external weights/audio required and installed package may omit training/examples |
| `3 / target/model-architecture.html` | `composite-config` [`TGT-CONFIG-001`]; `speaker-encoder` [`TGT-MODEL-001`]: 24kHz 128-bin mel → embedding; `talker` [`TGT-MODEL-002`]: text+codec → decoder → codec-0 logits; `code-predictor` [`TGT-MODEL-004`]: hidden state/prior codebooks → 15 residual groups; `precision-islands` [`TGT-MODEL-005,TGT-MODEL-006,TGT-MODEL-007`]: RoPE/RMSNorm/attention FP32 ranges; `generation-flow` [`TGT-MODEL-003,TGT-TOK25-011`]: prompt → Talker → MTP → speech tokenizer/generation config; `model-boundary`: static call map only |
| `4 / target/tokenizer-12hz.html` | `package-tokenizer-registry` [`TGT-PKG-002`]; `configuration` [`TGT-TOK12-002`]: 24kHz, stride 1920, 16 quantizers are verified; `rate-derivation` [`TGT-TOK12-003`]: `24000/1920=12.5 FPS` is separately labeled inference; `encode-contract` and `rvq` [`TGT-TOK12-001`]; `decode-contract` [`TGT-TOK12-001`]; `training-gap`: no public tokenizer training lifecycle in this tree |
| `5 / target/tokenizer-25hz.html` | `asset-inventory` [`TGT-TOK25-002`]: public executable checkpoint remains pending; `encoder-vq` [`TGT-TOK25-012,TGT-TOK25-013`]; `campplus-dependency` [`TGT-TOK25-003`]; `speech-vq-dependencies` [`TGT-TOK25-004,TGT-TOK25-005`]; `whisper-attention` [`TGT-TOK25-006,TGT-TOK25-007`]; `vq-core` [`TGT-TOK25-009,TGT-TOK25-010`]; `dit-bigvgan` [`TGT-TOK25-001`]; `decoder-precision` [`TGT-TOK25-008`]; `main-model-assets` [`TGT-TOK25-011`]; `asset-boundary`: split verified dependency/code facts from pending execution/public checkpoint |
| `6 / target/processor-contracts.html` | `text-contract` [`TGT-PROC-001`]: Qwen tokenizer/ChatML/BatchFeature; `audio-wrapper` [`TGT-PROC-002`]: normalize URL/path/base64/array then encode/decode; `shape-contract` [`TGT-PROC-001,TGT-PROC-002`]: text ids, `(T,16)` 12Hz codes, sample-rate/downsample metadata; `prompt-contract` [`TGT-PROC-001,TGT-PROC-002`]: x-vector-only versus ICL text+audio; `migration-boundary`: no Ascend claim |

Each page must contain: one learning objective list; prerequisite `熟悉 PyTorch 单卡张量与自回归生成`; every bracketed evidence ID above in its named section; at least one `call_chain` whose items name the exact symbols/path sequence stated above; a source table with exact target paths; a status/boundary section. Tests assert the exact section-ID set per page, every page evidence ID resolves, and each required call-chain label appears in order. The 25Hz page must visibly show both `已证实：静态依赖与源码路径` and `待真机验证：公开可执行性 unknown`; it must not collapse all VQ files under generic model evidence. All CUDA/BF16/FA2/FP32 teaching is descriptive of target defaults/precision only and contains no migration mapping.

- [ ] **Step 4: 构建九页并检查 immutable source links**

Run:

```bash
python3 -m unittest tests.test_site_builder -v
python3 scripts/build_site.py --output site --catalog content/site-foundation.json --catalog content/target-architecture.json
rg -n 'https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/' site/target
```

Expected: every discovered site-builder test passes; CLI reports 9 structural pages and one search index; every target page has at least one fixed-SHA link and no moving `/main/` source link.

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
        for text in ["finetuning/README.md", "TTSDataset.collate_fn", "outputs.loss + 0.3 * sub_talker_loss", "accelerator.prepare", "AdamW", "speaker row 3000", "CANN 8.5.2 兼容性：unknown"]:
            self.assertIn(text, serialized)
```

- [ ] **Step 2: 运行 test 并确认 training catalog 缺失**

Run: `python3 -m unittest tests.test_site_builder.SiteBuilderTest.test_full_catalog_has_thirteen_pages_and_required_training_sections -v`

Expected: FAIL with `FileNotFoundError: content/target-training.json`.

- [ ] **Step 3: 写入四页 official training catalog**

Create `content/target-training.json` with these exact contracts:

| Order / slug | Sections, call flow and mandatory boundary |
| --- | --- |
| `7 / target/sft-data-collate.html` | `public-recipe` [`TGT-SCOPE-001`]: only 12Hz Base single-speaker; `jsonl-contract` [`TGT-DATA-001`]: `audio/text/ref_audio` then `audio_codes`; `preprocess-device` [`TGT-DATA-003`]: default CUDA:0/device_map; `offline-codes` [`TGT-DATA-001`]: `prepare_data.main → tokenizer.encode → code.cpu().tolist → JSONL`; `dataset-item` and `collate-contract` [`TGT-DATA-002`]: text ids, `(T,16)`, 24kHz/128-bin ref mel, dual `(B,T,2)`, masks and codec-0 labels; `data-boundary`: no bucketing claim and sharding belongs to runtime discussion |
| `8 / target/sft-training-loop.html` | `target-precision-defaults` [`TGT-TRAIN-000`]: BF16+FA2 target default; `setup` [`TGT-TRAIN-001`]: model/config/dataset/dataloader → `accelerator.prepare`; `prepared-model-access` [`TGT-TRAIN-002,TGT-TRAIN-007`]: verified direct access to speaker_encoder/talker/custom method plus wrapper/version pending inference; `dataloader-sharding` [`TGT-TRAIN-006`]: Accelerate runtime takes ownership, behavior pending execution; `embedding-flow` [`TGT-TRAIN-002`]; `main-forward`/`sub-talker` [`TGT-MODEL-004,TGT-TRAIN-005`]; `training-loop` [`TGT-TRAIN-005`]: `outputs.loss + 0.3 * sub_talker_loss → accelerator.backward → clip → AdamW.step`; `training-boundary`: no scheduler/validation/resume/success claim |
| `9 / target/optimizer-checkpoint-export.html` | `accelerate-ownership` [`TGT-TRAIN-001,TGT-TRAIN-003,TGT-TRAIN-004,TGT-TRAIN-006,TGT-TRAIN-007`]: distinguish verified calls from inferred/pending process-local state/wrapper behavior; `optimizer` [`TGT-TRAIN-005`]: AdamW/clip; `repo-id-vs-local-path` [`TGT-EXPORT-002,TGT-EXPORT-003`]: default HF repo ID conflicts statically with copytree/direct config open, so actual export requires local directory; `main-process-export` [`TGT-EXPORT-001`]: lines 126 and 147-158; `custom-speaker` [`TGT-EXPORT-001`]: config rewrite, id 3000, drop speaker encoder, inject embedding; `checkpoint-gap` [`TGT-GAP-001`]: safetensors export is not optimizer/RNG resume |
| `10 / target/coverage-gaps.html` | `target-coverage`: all 35 dispositions; `reference-roles` [`PH1-ROLE-MM,PH1-ROLE-LLM,PH1-ROLE-MOSS`]: roles stay separate; `environment-lanes` [`PH1-ENV-LANES,TGT-HW-001`]: exact two lanes and 8.5.2 unknown; `future-validation`: import/device, operator/numerics, loss parity, audio/codec, checkpoint/inference, 8-card, multi-node, quality; `deferred-plans`: full reference walkthroughs, migration mapping, NPU execution |

Each page must contain the exact named section IDs and bracketed evidence IDs above, plus a call-chain block in the stated order. Tests compare these section sets and verify all evidence IDs resolve. The Accelerate page must say DataLoader sharding is handed to Accelerate runtime, not infer “no distributed sampler means no distribution”; wrapper/multi-process/global-speaker behavior is `inference`/pending execution and must not assert failure. The coverage page must distinguish documentation complete, source statically verified, project claim and hardware pending. It must say `本页不是迁移方案` and `本研究没有运行 CUDA、NPU、训练、推理或评测`. The project-native lane must not be described as reproduced, and target lane must remain unknown.

- [ ] **Step 4: 构建完整 13-page site**

Run:

```bash
python3 -m unittest tests.test_site_builder -v
python3 scripts/build_site.py --output site --catalog content/site-foundation.json --catalog content/target-architecture.json --catalog content/target-training.json
```

Expected: every discovered site-builder test passes; CLI reports 13 structural pages and one search index; orders are exactly 1 through 13 with distinct previous/next destinations.

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
- Modify: `IMPLEMENTATION_NOTES.md`

**Interfaces:**
- Consumes: complete 13-page site, content catalogs, 4 indexes, loaded evidence records, 35 coverage rows and existing Playwright shell behavior.
- Produces: `validate_generated_site(site_root: Path, pages: list[dict], evidence: dict[str, Evidence], coverage: list[dict]) -> list[str]`, `validate_cross_contracts(pages, evidence, coverage) -> list[str]`, `expected_generated_outputs(pages) -> set[str]`, `validate_fixed_links(site_root, registry) -> list[str]`, `validate_public_tracking(root) -> list[str]`; final `validate_phase2.py` gate and Playwright regressions.

- [ ] **Step 1: 写入 Python failing site validation tests**

Append these complete mutation helpers/tests; every test starts from a fresh generated copy and passes the same pages/evidence/coverage inputs used by production:

```python
import copy
import csv
import shutil
import tempfile

from scripts.phase2_contracts import (DECISION_REFS, load_evidence,
                                      validate_cross_contracts, validate_generated_site)
from scripts.site_builder import build_site, load_page_catalogs


def full_inputs():
    catalogs = [ROOT / "content/site-foundation.json", ROOT / "content/target-architecture.json", ROOT / "content/target-training.json"]
    pages = load_page_catalogs(catalogs)
    evidence = load_evidence(ROOT / "research/target-evidence.json")
    coverage = list(csv.DictReader((ROOT / "research/target-coverage.csv").open(encoding="utf-8")))
    return catalogs, pages, evidence, coverage


def generated_copy():
    context = tempfile.TemporaryDirectory()
    workspace = Path(context.name)
    root = workspace / "site"
    catalogs, pages, evidence, coverage = full_inputs()
    build_site(root, catalogs)
    for name in ("app.js", "theme.css", "layout.css"):
        destination = root / "assets" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "site" / "assets" / name, destination)
    for ref in DECISION_REFS:
        destination = workspace / ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ref, destination)
    return context, root, pages, evidence, coverage


def drop_page_evidence(pages, evidence_id):
    mutated = copy.deepcopy(pages)

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "evidence_ids":
                    value[key] = [item for item in child if item != evidence_id]
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(mutated)
    return mutated


class GeneratedSiteContractTest(unittest.TestCase):
    def test_broken_link_aria_and_remote_runtime_have_stable_errors(self):
        context, root, pages, evidence, coverage = generated_copy()
        self.addCleanup(context.cleanup)
        index = root / "index.html"
        html = index.read_text(encoding="utf-8")
        index.write_text(html.replace("</main>", '<a href="target/removed.html">x</a><button aria-controls="missing-node">x</button><script src="https://example.com/x.js"></script></main>'), encoding="utf-8")
        errors = validate_generated_site(root, pages, evidence, coverage)
        self.assertIn("index.html: broken local link target/removed.html", errors)
        self.assertIn("index.html: aria-controls missing-node has no matching id", errors)
        self.assertIn("index.html: remote runtime resource https://example.com/x.js", errors)

    def test_only_allowlisted_decision_links_may_leave_site_root(self):
        context, root, pages, evidence, coverage = generated_copy()
        self.addCleanup(context.cleanup)
        errors = validate_generated_site(root, pages, evidence, coverage)
        self.assertFalse(any("reference-selection-proposal.md" in error for error in errors))
        index = root / "index.html"
        html = index.read_text(encoding="utf-8")
        index.write_text(html.replace("</main>", '<a href="../IMPLEMENTATION_NOTES.md">escape</a></main>'), encoding="utf-8")
        self.assertIn("index.html: local link escapes site ../IMPLEMENTATION_NOTES.md",
                      validate_generated_site(root, pages, evidence, coverage))

    def test_coverage_catalog_evidence_and_important_bridge_mutations(self):
        _, pages, evidence, coverage = full_inputs()
        missing_path = [row for row in coverage if row["path"] != "qwen_tts/inference/qwen3_tts_model.py"]
        errors = validate_cross_contracts(pages, evidence, missing_path)
        self.assertIn("target coverage: missing qwen_tts/inference/qwen3_tts_model.py", errors)
        bad_section = copy.deepcopy(coverage)
        next(row for row in bad_section if row["path"] == "qwen_tts/core/__init__.py")["section"] = "missing"
        errors = validate_cross_contracts(pages, evidence, bad_section)
        self.assertIn("coverage qwen_tts/core/__init__.py: missing section target/tokenizer-12hz.html#missing", errors)
        bad_pages = copy.deepcopy(pages)
        bad_pages[2]["sections"][0]["blocks"][0]["evidence_ids"] = ["TGT-NOT-REAL"]
        errors = validate_cross_contracts(bad_pages, evidence, coverage)
        self.assertTrue(any("unknown evidence TGT-NOT-REAL" in error for error in errors))
        without_lane = drop_page_evidence(pages, "PH1-ENV-LANES")
        errors = validate_cross_contracts(without_lane, evidence, coverage)
        self.assertIn("important evidence PH1-ENV-LANES: not referenced by any page", errors)

    def test_unexpected_generated_output_is_rejected(self):
        context, root, pages, evidence, coverage = generated_copy()
        self.addCleanup(context.cleanup)
        stale = root / "target/stale.html"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale", encoding="utf-8")
        self.assertIn("site: unexpected generated output target/stale.html",
                      validate_generated_site(root, pages, evidence, coverage))
```

- [ ] **Step 2: 实现 stdlib HTML/link/heading/ARIA/offline validators**

Use `html.parser.HTMLParser` to collect tags, ids, headings, href/src/link rel, form action and ARIA references. For every one of 13 pages require: one `h1`; heading levels never jump by more than one; all relative href/action targets and fragments exist; all `aria-controls` values resolve; all runtime `script`, stylesheet, font, image and search data URLs are same-site relative; external anchor citations are allowed only over `https`; evidence status is in the four-state enum. `expected_generated_outputs(pages)` returns every page slug plus `assets/search-index.json`. Its comparison domain is exactly `site/**/*.html` plus `site/assets/search-index.json`; shared hand-maintained/modified `site/assets/app.js`, `theme.css`, `layout.css`, fonts and images are deliberately outside the generated exact-set/stale comparison. Reject missing/unexpected generated files, then byte-compare only that domain with a fresh temporary `build_site()` output.

```python
def expected_generated_outputs(pages) -> set[str]:
    return {page["slug"] for page in pages} | {"assets/search-index.json"}


def actual_generated_outputs(site_root: Path) -> set[str]:
    html = {path.relative_to(site_root).as_posix() for path in site_root.rglob("*.html")}
    search = site_root / "assets/search-index.json"
    return html | ({"assets/search-index.json"} if search.is_file() else set())
```

Use these exact catalog inputs for production and for the fresh deterministic rebuild. The optional argument keeps the four-argument public call valid while making the fresh-build dependency explicit and injectable in tests:

```python
PHASE2_CATALOG_PATHS = (
    ROOT / "content/site-foundation.json",
    ROOT / "content/target-architecture.json",
    ROOT / "content/target-training.json",
)


def _block_evidence_ids(block):
    yield from block.get("evidence_ids", [])
    for item in block.get("items", []):
        yield from item.get("evidence_ids", [])


def validate_cross_contracts(pages, evidence, coverage) -> list[str]:
    errors = []
    known_evidence = set(evidence)
    catalog = {page["slug"]: {section["id"]: section for section in page["sections"]}
               for page in pages}
    section_evidence = {}
    page_evidence = set()

    # 1. Validate page references first and derive references from pages, not
    #    from the evidence dictionary, so an important-ID omission is observable.
    for page in pages:
        for section in page["sections"]:
            refs = {evidence_id for block in section["blocks"]
                    for evidence_id in _block_evidence_ids(block)}
            section_evidence[(page["slug"], section["id"])] = refs
            page_evidence.update(refs)
            for evidence_id in sorted(refs - known_evidence):
                errors.append(f"page {page['slug']}#{section['id']}: unknown evidence {evidence_id}")

    # 2. Compare the coverage path multiset with the fixed target-index multiset.
    from scripts.site_builder import load_all_indexes
    target = load_all_indexes()["qwen3-tts-022e286b"]
    target_paths = collections.Counter(row["path"] for row in target["files"])
    coverage_paths = collections.Counter(row["path"] for row in coverage)
    for path in sorted((target_paths - coverage_paths).elements()):
        errors.append(f"target coverage: missing {path}")
    for path in sorted((coverage_paths - target_paths).elements()):
        errors.append(f"target coverage: unexpected {path}")

    # 3. Bridge each mapped/pending ledger row to its page, section and evidence.
    for row in coverage:
        if row["disposition"] not in {"mapped", "pending"}:
            continue
        destination = (row["page"], row["section"])
        if row["page"] not in catalog or row["section"] not in catalog[row["page"]]:
            errors.append(f"coverage {row['path']}: missing section {row['page']}#{row['section']}")
            continue
        for evidence_id in filter(None, row["evidence_ids"].split("|")):
            if evidence_id not in known_evidence:
                errors.append(f"coverage {row['path']}: unknown evidence {evidence_id}")
            elif evidence_id not in section_evidence[destination]:
                errors.append(f"coverage {row['path']}: evidence {evidence_id} absent from {row['page']}#{row['section']}")

    # 4. Evaluate important IDs last, against the page-derived union computed in
    #    phase 1. Deleting an Evidence record must not masquerade as a page omission.
    important = {"TGT-SCOPE-002", "TGT-TOK25-002", "PH1-ROLE-MM",
                 "PH1-ROLE-LLM", "PH1-ROLE-MOSS", "PH1-ENV-LANES"}
    for evidence_id in sorted(important - page_evidence):
        errors.append(f"important evidence {evidence_id}: not referenced by any page")
    return errors
```

Local-link validation uses `urllib.parse.urlsplit`, strips query/fragment only for filesystem resolution, and checks fragments against the parsed target page IDs. A local target may leave `site_root` only when its resolved path equals one of the two allowlisted decision files below and that file exists. Prefix matches, sibling files under `research/`, and every other `..` escape are rejected:

```python
def _resolve_local_target(site_root: Path, page_path: Path, href: str):
    parsed = urllib.parse.urlsplit(href)
    candidate = (page_path.parent / urllib.parse.unquote(parsed.path)).resolve()
    resolved_site = site_root.resolve()
    allowed = {(site_root.parent / ref).resolve() for ref in DECISION_REFS}
    if not candidate.is_relative_to(resolved_site):
        if candidate not in allowed:
            return None, f"{page_path.relative_to(site_root).as_posix()}: local link escapes site {href}"
        if not candidate.is_file():
            return None, f"{page_path.relative_to(site_root).as_posix()}: broken local link {href}"
    elif not candidate.is_file():
        return None, f"{page_path.relative_to(site_root).as_posix()}: broken local link {href}"
    return candidate, None


def validate_generated_site(site_root, pages, evidence, coverage,
                            catalog_paths=PHASE2_CATALOG_PATHS) -> list[str]:
    errors = validate_cross_contracts(pages, evidence, coverage)
    expected = expected_generated_outputs(pages)
    actual = actual_generated_outputs(site_root)
    for relative in sorted(expected - actual):
        errors.append(f"site: missing generated output {relative}")
    for relative in sorted(actual - expected):
        errors.append(f"site: unexpected generated output {relative}")

    parsed_pages = {}
    for relative in sorted(expected & actual):
        if not relative.endswith(".html"):
            continue
        path = site_root / relative
        parsed = parse_html(path)  # stdlib HTMLParser collector described above
        parsed_pages[path.resolve()] = parsed
        errors.extend(validate_document_structure(relative, parsed, evidence))

    for source_path, parsed in parsed_pages.items():
        for link in parsed.local_links:  # href, form action and same-site runtime URLs
            target, error = _resolve_local_target(site_root, source_path, link.url)
            if error:
                errors.append(error)
                continue
            if link.fragment and target.suffix == ".html":
                target_doc = parsed_pages.get(target) or parse_html(target)
                if link.fragment not in target_doc.ids:
                    errors.append(f"{source_path.relative_to(site_root).as_posix()}: broken fragment {link.url}")
        errors.extend(validate_aria_references(source_path, parsed))
        errors.extend(validate_remote_resources(source_path, parsed))

    # Compare only the declared generated domain. build_site is imported here,
    # never at phase2_contracts module import time, preserving one-way imports.
    with tempfile.TemporaryDirectory() as tmp:
        from scripts.site_builder import build_site
        fresh_root = Path(tmp) / "site"
        build_site(fresh_root, list(catalog_paths))
        for relative in sorted(expected):
            current, fresh = site_root / relative, fresh_root / relative
            if current.is_file() and fresh.is_file() and current.read_bytes() != fresh.read_bytes():
                errors.append(f"site: generated output differs {relative}")
    return errors
```

`validate_document_structure` performs the one-h1, non-skipping heading, four-state evidence-status and runtime-resource checks. `validate_remote_resources` rejects every remote script, stylesheet, font, image and search-data URL; only anchor citations with an `https` scheme are accepted. `validate_aria_references` checks every token in every `aria-controls` value against IDs in the same document. Exact stable mutation errors are those asserted in Step 1.

Extend `validate_phase2.py` success output to exactly:

```text
validated Phase 2: 4 indexes / 3270 files, {len(evidence)} evidence records, 35 coverage rows, 13 pages, 0 broken links, 0 omissions
```

Render the `{len(evidence)}` field at runtime from the loaded evidence dict and assert that the printed integer equals it; do not maintain an independent numeric evidence constant.

- [ ] **Step 3: 泛化 existing template tests to generated homepage**

Update old HCCL/MindSpeed-specific assertions, not the stable shell behavior. `template-structure.spec.js` keeps semantic regions, one h1, local resources, tokens and no-script evidence. `final-review-regressions.spec.js` uses target commit constant `022e286b98fbec7e1e916cb940cdf532cd9f488e`, expects a Qwen fixed blob URL and copies a short Qwen excerpt; all rail, drawer, tree, print and 200% tests remain. `template-visual.spec.js` continues the 1440×900, 1024×768 and 390×844 homepage baselines.

- [ ] **Step 4: 写入 multi-page navigation/search tests**

Create `tests/site/phase2-navigation-search.spec.js` with these tests (plus the index/coverage assertions below):

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

test('loaded site keeps inline search working after browser goes offline', async ({ page, context }) => {
  const requests = [];
  page.on('request', (request) => requests.push(request.url()));
  await page.goto('/site/search.html');
  await context.setOffline(true);
  await page.locator('#site-search input[name=q]').fill('forward_sub_talker_finetune');
  await page.locator('#site-search').press('Enter');
  await expect(page.getByRole('status')).toContainText('找到');
  await expect(page.getByRole('link', { name: /forward_sub_talker_finetune/ })).toBeVisible();
  expect(requests.every((url) => new URL(url).origin === new URL(page.url()).origin)).toBe(true);
});

test('nested target search form resolves to root search results', async ({ page }) => {
  await page.goto('/site/target/model-architecture.html');
  await page.locator('#site-search input[name=q]').fill('RMSNorm');
  await Promise.all([
    page.waitForURL(/\/site\/search\.html\?q=RMSNorm$/),
    page.locator('#site-search').press('Enter'),
  ]);
  await expect(page.getByRole('status')).toContainText('找到');
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

Create `tests/site/phase2-responsive-accessibility.spec.js` with this shared axe helper and five executable tests:

```javascript
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

async function expectNoAxeViolations(page) {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(result.violations, JSON.stringify(result.violations, null, 2)).toEqual([]);
}

test('desktop architecture page is WCAG A/AA clean', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/site/target/model-architecture.html');
  await expectNoAxeViolations(page);
});

test('laptop data page is WCAG A/AA clean', async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto('/site/target/sft-data-collate.html');
  await expectNoAxeViolations(page);
});

test('mobile coverage drawers remain accessible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/site/target/coverage-gaps.html');
  await page.locator('#toggle-left').click();
  await expect(page.locator('#chapter-nav')).toBeVisible();
  await expectNoAxeViolations(page);
  await page.locator('#toggle-left').click();
  await page.locator('#toggle-right').click();
  await expect(page.locator('#evidence-rail')).toBeVisible();
  await expectNoAxeViolations(page);
});

test('JavaScript-disabled site retains article evidence and static directory', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('/site/search.html');
  await expect(page.locator('#article-content')).toContainText('全站搜索');
  await expect(page.locator('#no-script-index a')).toHaveCount(13);
  await page.goto('/site/target/model-architecture.html');
  await expect(page.locator('#article-content')).toContainText('模型');
  await expect(page.locator('#evidence-rail a[href^="https://"]')).not.toHaveCount(0);
  await context.close();
});

test('720 CSS pixels at 200 percent has no document overflow', async ({ page }) => {
  await page.setViewportSize({ width: 720, height: 800 });
  await page.goto('/site/target/coverage-gaps.html');
  await expect(page.locator('.table-scroll')).not.toHaveCount(0);
  const metrics = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth,
    tableScrollable: [...document.querySelectorAll('.table-scroll')].some((node) => node.scrollWidth > node.clientWidth) }));
  expect(metrics.scroll).toBeLessThanOrEqual(metrics.client);
  expect(metrics.tableScrollable).toBe(true);
});
```

- [ ] **Step 6: 运行 Python validators and suites**

Run:

```bash
python3 scripts/validate_phase2.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Expected: validator prints the dynamic evidence count and fixed 4/3270/35/13 structural counts; all discovered Python tests pass; whitespace check has no output.

- [ ] **Step 7: 更新并复验三视口 screenshots**

Run:

```bash
npm run test:update-snapshots -- tests/site/template-visual.spec.js
npm test -- tests/site/template-visual.spec.js
```

Expected: the three structural viewport baselines update once; the second command reports every discovered visual test passing with no diff.

- [ ] **Step 8: 运行完整 Playwright suite**

Run: `npm test`

Expected: every discovered Playwright test passes; report the runner's actual total instead of a hand-maintained expected count.

- [ ] **Step 9: 运行 final public-content and actual-path audit**

Run:

```bash
git ls-files | rg '(^|/)\.superpowers/source-checkouts/|\.(safetensors|ckpt|pt|pth|onnx|gguf|wav|mp3|m4a|flac)$|(^|/)(weights|datasets|checkpoints)(/|$)' && exit 1 || true
rg -ni 'to''do|tb''d|place''holder|lorem'' ipsum' content research/indexes research/target-evidence.json research/target-coverage.csv site scripts tests
rg -n '/Users/|[A-Za-z]:\\\\' research/indexes site/assets/search-index.json
for path in finetuning/README.md finetuning/dataset.py finetuning/sft_12hz.py qwen_tts/core/models/modeling_qwen3_tts.py qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py; do test -f ".superpowers/source-checkouts/qwen3-tts-022e286b/$path"; done
git status --short
```

Expected: restricted tracking, red-flag-token and absolute-path scans have no output; all six verified target paths exist; status lists only Task 8 intended files before commit.

- [ ] **Step 10: 记录 Phase 2 completion/deviations/deferred work**

Append a dated `Phase 2 target walkthrough completion` entry to `IMPLEMENTATION_NOTES.md` with: generated 13-page scope; actual derived evidence/test counts; local-HTTP/browser-offline definition; implementation deviations from this plan; identity limitation inherited from Task 3; no CUDA/NPU/model execution; CANN 8.5.2 unknown; and the unchanged deferrals (full MM/LLM/MOSS walkthroughs, migration mapping, 8-card/multi-node/NPU execution).

- [ ] **Step 11: 提交 completion gates**

```bash
git add scripts/phase2_contracts.py scripts/validate_phase2.py tests/test_phase2_contracts.py tests/site IMPLEMENTATION_NOTES.md
git commit -m "test: verify Phase 2 target walkthrough"
```

Expected: one commit; validator, Python tests and all discovered Playwright tests remain green; no push occurs.

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
- The dynamically counted bounded evidence records use all four states, resolve every `source_id` against the Phase 1 ledger, and 35 target files have exactly one mapped/excluded/pending disposition.
- The generated site has exactly 13 coverage-driven pages, one `h1` each, complete previous/next navigation, local inline search and no broken local links/fragments.
- Python and Playwright report their actual discovered totals with zero failures across desktop, laptop, mobile, 200% reflow, browser-offline, no-script and axe cases.
- No tracked source tree, weight, dataset, checkpoint, LFS object, secret, restricted media, absolute local path or full source body exists.
- The content visibly preserves PyTorch single-card teaching, both environment lanes, CANN 8.5.2 unknown status and all deferred later-plan boundaries.
