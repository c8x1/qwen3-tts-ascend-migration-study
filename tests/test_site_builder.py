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
    load_page_catalogs,
    relative_href,
    render_page,
    script_safe_json,
    validate_catalogs,
)


ROOT = Path(__file__).resolve().parents[1]


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
