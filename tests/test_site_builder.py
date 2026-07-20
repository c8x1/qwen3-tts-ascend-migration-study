import copy
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from scripts import build_site as build_site_cli
from scripts.phase2_contracts import Evidence
from scripts.site_builder import (
    build_search_documents,
    build_site,
    decision_href,
    load_all_indexes,
    load_page_catalogs,
    relative_href,
    render_page,
    script_safe_json,
    validate_catalogs,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET_CATALOGS = [
    ROOT / "content/site-foundation.json",
    ROOT / "content/target-architecture.json",
]
TARGET_FIXED_PREFIX = (
    "https://github.com/QwenLM/Qwen3-TTS/blob/"
    "022e286b98fbec7e1e916cb940cdf532cd9f488e/"
)
TARGET_PAGE_CONTRACTS = {
    "target/package-inference-api.html": {
        "order": 2,
        "title": "包结构与推理 API",
        "sections": {
            "package-layout": {
                "TGT-PKG-001", "TGT-PKG-002", "TGT-PKG-003",
                "TGT-PKG-004", "TGT-PKG-005", "TGT-PKG-006",
            },
            "target-defaults": {"TGT-CLI-001", "TGT-CLI-002"},
            "load-chain": {"TGT-API-001"},
            "base-api": {"TGT-API-002"},
            "voice-design-api": {"TGT-API-003"},
            "custom-api": {"TGT-API-003"},
            "package-boundary": set(),
        },
        "call_chain": [
            ("公开入口", "qwen_tts/inference/qwen3_tts_model.py", "Qwen3TTSModel.from_pretrained"),
            ("注册配置", "qwen_tts/inference/qwen3_tts_model.py", "AutoConfig.register"),
            ("装载模型", "qwen_tts/inference/qwen3_tts_model.py", "AutoModel.from_pretrained"),
            ("装载处理器", "qwen_tts/inference/qwen3_tts_model.py", "AutoProcessor.from_pretrained"),
        ],
        "boundary": "package-boundary",
    },
    "target/model-architecture.html": {
        "order": 3,
        "title": "复合模型架构与生成流",
        "sections": {
            "composite-config": {"TGT-CONFIG-001"},
            "speaker-encoder": {"TGT-MODEL-001"},
            "talker": {"TGT-MODEL-002"},
            "code-predictor": {"TGT-MODEL-004"},
            "precision-islands": {"TGT-MODEL-005", "TGT-MODEL-006", "TGT-MODEL-007"},
            "generation-flow": {"TGT-MODEL-003", "TGT-TOK25-011"},
            "model-boundary": set(),
        },
        "call_chain": [
            ("提示词与说话人条件", "qwen_tts/core/models/modeling_qwen3_tts.py", "Qwen3TTSForConditionalGeneration"),
            ("Talker codec-0", "qwen_tts/core/models/modeling_qwen3_tts.py", "Qwen3TTSTalkerForConditionalGeneration"),
            ("MTP 残差码本", "qwen_tts/core/models/modeling_qwen3_tts.py", "forward_sub_talker_finetune"),
            ("语音 tokenizer 与生成配置", "qwen_tts/core/models/modeling_qwen3_tts.py", "speech_tokenizer/* + generation_config.json"),
        ],
        "boundary": "model-boundary",
    },
    "target/tokenizer-12hz.html": {
        "order": 4,
        "title": "12Hz Tokenizer 契约",
        "sections": {
            "package-tokenizer-registry": {"TGT-PKG-002"},
            "configuration": {"TGT-TOK12-002"},
            "rate-derivation": {"TGT-TOK12-003"},
            "encode-contract": {"TGT-TOK12-001"},
            "rvq": {"TGT-TOK12-001"},
            "decode-contract": {"TGT-TOK12-001"},
            "training-gap": set(),
        },
        "call_chain": [
            ("编码入口", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "Qwen3TTSTokenizerV2Model.encode"),
            ("残差量化", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "SplitResidualVectorQuantizer"),
            ("解码入口", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "Qwen3TTSTokenizerV2Model.decode"),
        ],
        "boundary": "training-gap",
    },
    "target/tokenizer-25hz.html": {
        "order": 5,
        "title": "25Hz Tokenizer 静态依赖图",
        "sections": {
            "asset-inventory": {"TGT-TOK25-002"},
            "encoder-vq": {"TGT-TOK25-012", "TGT-TOK25-013"},
            "campplus-dependency": {"TGT-TOK25-003"},
            "speech-vq-dependencies": {"TGT-TOK25-004", "TGT-TOK25-005"},
            "whisper-attention": {"TGT-TOK25-006", "TGT-TOK25-007"},
            "vq-core": {"TGT-TOK25-009", "TGT-TOK25-010"},
            "dit-bigvgan": {"TGT-TOK25-001"},
            "decoder-precision": {"TGT-TOK25-008"},
            "main-model-assets": {"TGT-TOK25-011"},
            "asset-boundary": set(),
        },
        "call_chain": [
            ("Tokenizer 入口", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Model"),
            ("编码与量化", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Encoder"),
            ("VQ 核心", "qwen_tts/core/tokenizer_25hz/vq/core_vq.py", "DistributedGroupResidualVectorQuantization"),
            ("解码与波形", "qwen_tts/core/tokenizer_25hz/modeling_qwen3_tts_tokenizer_v1.py", "Qwen3TTSTokenizerV1Decoder"),
        ],
        "boundary": "asset-boundary",
    },
    "target/processor-contracts.html": {
        "order": 6,
        "title": "Processor 输入与提示词契约",
        "sections": {
            "text-contract": {"TGT-PROC-001"},
            "audio-wrapper": {"TGT-PROC-002"},
            "shape-contract": {"TGT-PROC-001", "TGT-PROC-002"},
            "prompt-contract": {"TGT-PROC-001", "TGT-PROC-002"},
            "migration-boundary": set(),
        },
        "call_chain": [
            ("输入归一化", "qwen_tts/inference/qwen3_tts_tokenizer.py", "Qwen3TTSTokenizer._normalize_audio_inputs"),
            ("文本与 ChatML", "qwen_tts/core/models/processing_qwen3_tts.py", "Qwen3TTSProcessor"),
            ("音频编码", "qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py", "Qwen3TTSTokenizerV2Model.encode"),
            ("提示词分支", "qwen_tts/inference/qwen3_tts_model.py", "x-vector-only / ICL text+audio"),
        ],
        "boundary": "migration-boundary",
    },
}


def minimal_catalog(block=None, text="x"):
    block = block or {
        "type": "paragraph",
        "text": text,
        "state": "verified",
        "evidence_ids": ["E-1"],
    }
    return {
        "schema_version": 1,
        "pages": [
            {
                "slug": "index.html",
                "title": "Title",
                "summary": "Summary",
                "order": 1,
                "group": "foundation",
                "objectives": ["Learn"],
                "prerequisites": ["PyTorch"],
                "sections": [
                    {"id": "intro", "title": "Intro", "blocks": [block]}
                ],
            }
        ],
    }


def fixture_indexes():
    return {
        "snap": {
            "files": [
                {
                    "path": "pkg/a.py",
                    "bytes": 4,
                    "sha256": "a" * 64,
                    "kind": "python",
                    "line_count": 2,
                }
            ],
            "symbols": [
                {
                    "id": "pkg/a.py:C:1",
                    "path": "pkg/a.py",
                    "qualname": "C",
                    "kind": "class",
                    "line": 1,
                    "end_line": 2,
                }
            ],
            "configs": [
                {
                    "id": "pkg/a.py:FLAG:2",
                    "path": "pkg/a.py",
                    "key": "FLAG",
                    "owner": "",
                    "kind": "python-assignment",
                    "line": 2,
                }
            ],
        }
    }


def fixture_evidence(decision_refs=()):
    return {
        "E-1": Evidence(
            "E-1",
            None,
            None,
            None,
            None,
            "verified",
            "claim",
            "",
            ("SRC-001",),
            decision_refs,
        )
    }


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        attribute = "href" if tag in {"a", "link"} else "src" if tag == "script" else None
        if attribute and values.get(attribute):
            self.links.append(values[attribute])


class SiteBuilderTest(unittest.TestCase):
    def test_cli_default_catalogs_load_only_approved_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "content"
            content.mkdir()
            for name in (
                "site-foundation.json",
                "target-architecture.json",
                "target-training.json",
                "site-architecture.json",
                "site-training.json",
            ):
                (content / name).write_text("{}", encoding="utf-8")
            with patch.object(build_site_cli, "ROOT", root):
                self.assertEqual(
                    build_site_cli.default_catalogs(),
                    [
                        content / "site-foundation.json",
                        content / "target-architecture.json",
                        content / "target-training.json",
                    ],
                )

    def test_foundation_build_is_deterministic_and_has_four_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            pages = build_site(output, [ROOT / "content/site-foundation.json"])
            first = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in pages
            }
            pages_again = build_site(
                output, [ROOT / "content/site-foundation.json"]
            )
            second = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in pages_again
            }
            self.assertEqual(first, second)
            self.assertEqual(
                set(first),
                {
                    "index.html",
                    "indexes/source-files.html",
                    "indexes/symbols-configs.html",
                    "search.html",
                    "assets/search-index.json",
                },
            )

    def test_generated_shell_escapes_content_and_uses_local_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "index.html").read_text(encoding="utf-8")
            for element_id in (
                "chapter-nav",
                "article-content",
                "evidence-rail",
                "toggle-left",
                "toggle-right",
                "site-search",
                "chapter-tree",
                "page-toc",
            ):
                self.assertIn(f'id="{element_id}"', html)
            self.assertNotIn("https://fonts", html)
            self.assertIn('src="assets/app.js"', html)
            self.assertEqual(html.count("<h1>"), 1)
            self.assertTrue(
                all(line == line.rstrip() for line in html.splitlines())
            )

    def test_page_catalog_has_unique_order_slug_and_section_ids(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        self.assertEqual(len({page["slug"] for page in pages}), len(pages))
        self.assertEqual(len({page["order"] for page in pages}), len(pages))
        for page in pages:
            ids = [section["id"] for section in page["sections"]]
            self.assertEqual(len(ids), len(set(ids)))

    def test_inline_search_json_cannot_close_its_script_element(self):
        encoded = script_safe_json(
            [{"title": "</script><img src=x onerror=alert(1)>&"}]
        )
        self.assertNotIn("</script", encoded.lower())
        self.assertIn(r"\u003c/script", encoded)
        self.assertIn(r"\u003e", encoded)
        self.assertIn(r"\u0026", encoded)

    def test_every_page_search_form_targets_relative_search_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            self.assertIn(
                'action="search.html"',
                (output / "index.html").read_text(encoding="utf-8"),
            )
            self.assertIn(
                'action="../search.html"',
                (output / "indexes/source-files.html").read_text(
                    encoding="utf-8"
                ),
            )

    def test_catalog_validator_rejects_unknown_evidence_and_block_field(self):
        data = minimal_catalog(
            block={
                "type": "paragraph",
                "text": "x",
                "state": "verified",
                "evidence_ids": ["MISSING"],
                "raw_html": "<b>x</b>",
            }
        )
        errors = validate_catalogs(data, set())
        self.assertIn(
            "catalog.pages[0].sections[0].blocks[0]: unknown field raw_html",
            errors,
        )
        data = minimal_catalog(
            block={
                "type": "paragraph",
                "text": "x",
                "state": "verified",
                "evidence_ids": ["MISSING"],
            }
        )
        errors = validate_catalogs(data, set())
        self.assertIn(
            "catalog.pages[0]#intro: unknown evidence MISSING", errors
        )

    def test_catalog_validator_is_total_for_malformed_containers_and_union(self):
        malformed = [
            None,
            [],
            {},
            {"schema_version": 1, "pages": None},
            {"schema_version": 1, "pages": [None]},
        ]
        for data in malformed:
            with self.subTest(data=data):
                errors = validate_catalogs(data, set())
                self.assertIsInstance(errors, list)
                self.assertTrue(errors)

        for block in (
            {"type": "unknown"},
            {"type": "paragraph", "text": "x"},
            {
                "type": "table",
                "headers": ["a", "b"],
                "rows": [["only one"]],
            },
        ):
            with self.subTest(block=block):
                errors = validate_catalogs(minimal_catalog(block=block), {"E-1"})
                self.assertTrue(errors)

    def test_relative_href_and_search_anchor_contract(self):
        self.assertEqual(
            relative_href("target/model.html", "search.html"), "../search.html"
        )
        self.assertEqual(
            decision_href(
                "index.html", "research/reference-selection-proposal.md"
            ),
            "../research/reference-selection-proposal.md",
        )
        self.assertEqual(
            decision_href(
                "target/model.html",
                "research/reference-selection-proposal.md",
            ),
            "../../research/reference-selection-proposal.md",
        )
        documents = build_search_documents(
            minimal_catalog()["pages"], fixture_indexes()
        )
        self.assertEqual(
            documents,
            sorted(
                documents,
                key=lambda row: (row["kind"], row["title"], row["href"]),
            ),
        )
        symbol = next(row for row in documents if row["kind"] == "symbol")
        self.assertRegex(
            symbol["href"],
            r"^indexes/symbols-configs\.html#entry-[0-9a-f]{16}$",
        )

    def test_search_metadata_is_complete_without_source_body_or_values(self):
        documents = build_search_documents(
            minimal_catalog()["pages"], fixture_indexes()
        )
        self.assertEqual(
            {doc["kind"] for doc in documents},
            {"page", "file", "symbol", "config"},
        )
        for document in documents:
            self.assertNotIn("body", document)
            self.assertNotIn("source", document)
            self.assertNotIn("value", document)
        self.assertIn("pkg/a.py", next(d for d in documents if d["kind"] == "file")["searchable"])
        self.assertIn("c", next(d for d in documents if d["kind"] == "symbol")["searchable"])
        self.assertIn("flag", next(d for d in documents if d["kind"] == "config")["searchable"])

    def test_render_resolves_evidence_decisions_and_escapes_all_values(self):
        page = minimal_catalog(text='<img src=x onerror="boom">')["pages"][0]
        html = render_page(
            page,
            [page],
            fixture_evidence(
                decision_refs=("research/reference-selection-proposal.md",)
            ),
            [],
        )
        self.assertIn('id="chapter-nav"', html)
        self.assertIn('id="article-content"', html)
        self.assertIn('id="evidence-rail"', html)
        self.assertIn(
            'href="../research/reference-selection-proposal.md"', html
        )
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;img", html)

    def test_render_rejects_unknown_evidence_unsupported_block_and_bad_rows(self):
        page = minimal_catalog()["pages"][0]
        with self.assertRaisesRegex(
            ValueError, r"page index\.html#intro: unknown evidence E-1"
        ):
            render_page(page, [page], {}, [])

        unsupported = copy.deepcopy(page)
        unsupported["sections"][0]["blocks"] = [{"type": "future"}]
        with self.assertRaisesRegex(ValueError, r"block future: unsupported"):
            render_page(unsupported, [unsupported], fixture_evidence(), [])

        bad_table = copy.deepcopy(page)
        bad_table["sections"][0]["blocks"] = [
            {"type": "table", "headers": ["a", "b"], "rows": [["one"]]}
        ]
        with self.assertRaisesRegex(
            ValueError, r"table intro: row width 1 expected 2"
        ):
            render_page(bad_table, [bad_table], fixture_evidence(), [])

    def test_foundation_content_contract(self):
        pages = load_page_catalogs([ROOT / "content/site-foundation.json"])
        self.assertEqual(len(pages), 4)
        expected_sections = {
            "index.html": {
                "public-scope",
                "learning-path",
                "environment-lanes",
                "phase-boundary",
            },
            "indexes/source-files.html": {
                "snapshot-provenance",
                "file-filters",
                "future-interface",
            },
            "indexes/symbols-configs.html": {
                "symbol-index",
                "config-index",
                "limits",
            },
            "search.html": {
                "search-results",
                "no-script-index",
                "search-scope",
            },
        }
        for page in pages:
            self.assertTrue(page["objectives"])
            self.assertIn(
                "熟悉 PyTorch 单卡张量与训练循环", page["prerequisites"]
            )
            self.assertEqual(
                {section["id"] for section in page["sections"]},
                expected_sections[page["slug"]],
            )

        homepage = next(page for page in pages if page["slug"] == "index.html")
        homepage_json = json.dumps(homepage, ensure_ascii=False)
        self.assertIn("本阶段没有运行 Qwen3-TTS 训练。", homepage_json)
        self.assertIn("CANN 8.5.2 兼容性：unknown，待真机验证。", homepage_json)
        for package in (
            "目标源码架构走读",
            "MindSpeed-MM 训练栈映射",
            "分布式与性能契约",
            "环境与兼容性验证",
            "单机到规模化 SFT 教程",
        ):
            self.assertIn(package, homepage_json)

    def test_architecture_catalog_covers_required_target_symbols(self):
        pages = load_page_catalogs(TARGET_CATALOGS)
        self.assertEqual(len(pages), 9)
        targets = [page for page in pages if page["group"] == "target-architecture"]
        self.assertEqual(
            [(page["order"], page["slug"], page["title"]) for page in targets],
            [
                (
                    contract["order"],
                    slug,
                    contract["title"],
                )
                for slug, contract in TARGET_PAGE_CONTRACTS.items()
            ],
        )

        for page in targets:
            with self.subTest(slug=page["slug"]):
                contract = TARGET_PAGE_CONTRACTS[page["slug"]]
                sections = {
                    section["id"]: section for section in page["sections"]
                }
                self.assertEqual(set(sections), set(contract["sections"]))
                self.assertTrue(page["objectives"])
                self.assertEqual(
                    page["prerequisites"],
                    ["熟悉 PyTorch 单卡张量与自回归生成"],
                )

                for section_id, expected_evidence in contract["sections"].items():
                    actual_evidence = set()
                    for block in sections[section_id]["blocks"]:
                        actual_evidence.update(block.get("evidence_ids", []))
                        for item in block.get("items", []):
                            actual_evidence.update(item.get("evidence_ids", []))
                    self.assertTrue(
                        expected_evidence <= actual_evidence,
                        f"{page['slug']}#{section_id}: "
                        f"missing {expected_evidence - actual_evidence}",
                    )

                chains = [
                    block
                    for section in page["sections"]
                    for block in section["blocks"]
                    if block["type"] == "call_chain"
                ]
                self.assertTrue(chains)
                self.assertEqual(
                    [
                        (item["label"], item["path"], item["symbol"])
                        for item in chains[0]["items"]
                    ],
                    contract["call_chain"],
                )
                source_tables = [
                    block
                    for section in page["sections"]
                    for block in section["blocks"]
                    if block["type"] == "table"
                    and "源码路径" in block["headers"]
                    and block["rows"]
                ]
                self.assertTrue(source_tables)
                self.assertTrue(sections[contract["boundary"]]["blocks"])

        serialized = json.dumps(targets, ensure_ascii=False)
        for symbol in (
            "Qwen3TTSModel.from_pretrained",
            "Qwen3TTSForConditionalGeneration",
            "Qwen3TTSTalkerForConditionalGeneration",
            "forward_sub_talker_finetune",
            "Qwen3TTSSpeakerEncoder",
            "Qwen3TTSTokenizerV2Model",
            "Qwen3TTSTokenizerV1Model",
            "Qwen3TTSProcessor",
        ):
            self.assertIn(symbol, serialized)
        self.assertIn("已证实：静态依赖与源码路径", serialized)
        self.assertIn("待真机验证：公开可执行性 unknown", serialized)
        self.assertIn("24000/1920=12.5 FPS", serialized)
        self.assertIn("推断", serialized)
        self.assertIn("sdist", serialized)
        self.assertIn("不等于源码仓中不存在 examples/finetuning", serialized)
        self.assertIn("codec-0", serialized)
        self.assertIn("15 个残差码本组", serialized)
        self.assertIn("(T,16)", serialized)
        self.assertIn("x-vector-only", serialized)
        self.assertIn("ICL text+audio", serialized)
        self.assertNotRegex(serialized, r"CANN 8\.5\.2.*(?:兼容|支持|跑通)")
        self.assertNotRegex(serialized, r"(?:Ascend|昇腾).*(?:兼容|支持|跑通)")

    def test_generated_architecture_site_preserves_navigation_search_and_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            built = build_site(output, TARGET_CATALOGS)
            html_paths = [path for path in built if path.suffix == ".html"]
            self.assertEqual(len(html_paths), 9)

            pages = load_page_catalogs(TARGET_CATALOGS)
            indexes = load_all_indexes()
            expected_document_count = len(pages) + sum(
                len(index[dataset])
                for index in indexes.values()
                for dataset in ("files", "symbols", "configs")
            )
            self.assertEqual(expected_document_count, 47_500)
            external = json.loads(
                (output / "assets/search-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(len(external), expected_document_count)

            search_html = (output / "search.html").read_text(encoding="utf-8")
            match = re.search(
                r'<script id="search-data" type="application/json">(.*?)</script>',
                search_html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            self.assertEqual(json.loads(match.group(1)), external)

            expected_nav = [
                (page["order"], page["title"]) for page in pages
            ]
            for path in html_paths:
                html = path.read_text(encoding="utf-8")
                self.assertEqual(html.count("<h1>"), 1)
                nav = re.search(
                    r'<ul id="chapter-tree" class="chapter-tree">(.*?)</ul>',
                    html,
                    re.DOTALL,
                )
                self.assertIsNotNone(nav)
                self.assertEqual(
                    [
                        (int(order), title)
                        for order, title in re.findall(
                            r">(\d+) · ([^<]+)</a>", nav.group(1)
                        )
                    ],
                    expected_nav,
                )

                parser = LinkParser()
                parser.feed(html)
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                for href in parser.links:
                    if href.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    target_text = href.split("#", 1)[0].split("?", 1)[0]
                    if target_text.endswith(".html"):
                        target = (path.parent / target_text).resolve()
                        self.assertTrue(
                            target.is_file(),
                            f"{path.relative_to(output)} -> {href}",
                        )

            for slug in TARGET_PAGE_CONTRACTS:
                html = (output / slug).read_text(encoding="utf-8")
                self.assertIn(TARGET_FIXED_PREFIX, html)
                self.assertNotIn("github.com/QwenLM/Qwen3-TTS/blob/main/", html)
                self.assertIn('class="rail-card evidence-card"', html)
                self.assertGreaterEqual(html.count('data-state="'), 2)
                self.assertGreaterEqual(
                    html.count('data-evidence-state="'), 2
                )

    def test_search_page_inline_documents_match_file_and_runtime_is_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            build_site(output, [ROOT / "content/site-foundation.json"])
            html = (output / "search.html").read_text(encoding="utf-8")
            match = re.search(
                r'<script id="search-data" type="application/json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            inline = json.loads(match.group(1))
            external = json.loads(
                (output / "assets/search-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(inline, external)
            metadata = [doc for doc in inline if doc["kind"] != "page"]
            expected_snapshots = {
                "qwen3-tts-022e286b",
                "mindspeed-mm-0edd553e",
                "mindspeed-llm-434baff7",
                "moss-tts-ad99ec5f",
            }
            self.assertEqual(
                {doc["summary"] for doc in metadata}, expected_snapshots
            )
            for snapshot_id in expected_snapshots:
                self.assertEqual(
                    {
                        doc["kind"]
                        for doc in metadata
                        if doc["summary"] == snapshot_id
                    },
                    {"file", "symbol", "config"},
                )
            parser = LinkParser()
            parser.feed(html)
            self.assertEqual(len(parser.ids), len(set(parser.ids)))
            self.assertIn('class="search-results"', html)
            self.assertIn('id="search-results-status"', html)
            self.assertIn('id="no-script-index"', html)
            self.assertNotRegex(
                html,
                r'<(?:script|link)[^>]+(?:src|href)="https?://',
            )

            app = (ROOT / "site/assets/app.js").read_text(encoding="utf-8")
            self.assertNotIn("fetch(", app)
            self.assertIn("replaceChildren", app)
            self.assertIn("textContent", app)
            self.assertIn("replaceState", app)

    def test_generated_local_links_resolve_within_current_foundation(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            built = build_site(output, [ROOT / "content/site-foundation.json"])
            html_paths = [path for path in built if path.suffix == ".html"]
            for path in html_paths:
                parser = LinkParser()
                parser.feed(path.read_text(encoding="utf-8"))
                for href in parser.links:
                    if href.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    target_text = href.split("#", 1)[0].split("?", 1)[0]
                    if not target_text.endswith(".html"):
                        continue
                    target = (path.parent / target_text).resolve()
                    self.assertTrue(
                        target.is_file(),
                        f"{path.relative_to(output)} -> {href}",
                    )

    def test_css_tokens_and_breakpoints_are_preserved(self):
        theme = (ROOT / "site/assets/theme.css").read_text(encoding="utf-8")
        layout = (ROOT / "site/assets/layout.css").read_text(encoding="utf-8")
        for declaration in (
            "--canvas: #f7f1e7",
            "--header: #e8ddcd",
            "--left-bg: #eee5d8",
            "--article-bg: #fcf9f3",
            "--right-bg: #f1e8dc",
            "--ink: #2b251f",
            "--accent: #934735",
            "--code-bg: #22211e",
        ):
            self.assertIn(declaration, theme)
        self.assertIn("@media (max-width: 1199px)", layout)
        self.assertIn("@media (max-width: 720px)", layout)
        self.assertIn("@media (max-width: 390px)", layout)
        self.assertIn(".status-grid", theme)
        self.assertIn(".contract-table", theme)
        self.assertIn(".index-table", theme)
        self.assertIn(".search-results", theme)
        self.assertIn(".evidence-state", theme)


if __name__ == "__main__":
    unittest.main()
