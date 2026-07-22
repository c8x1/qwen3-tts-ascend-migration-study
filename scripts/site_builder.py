"""Deterministic static-site builder for page catalogs and source indexes."""

from __future__ import annotations

import hashlib
import html
import json
import posixpath
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from scripts.phase2_contracts import (
    DECISION_REFS,
    Evidence,
    fixed_url,
    load_evidence,
    load_snapshot_registry,
    validate_against_schema,
)
from scripts.phase3_contracts import load_reference_evidence


ROOT = Path(__file__).resolve().parents[1]

STATE_LABELS = {
    "verified": "已核验",
    "project_claim": "项目声明",
    "inference": "静态推断",
    "pending_hardware": "待真机验证",
}

NAVIGATION_TRACKS = ("入门教程", "源码深读", "实施路线")


@lru_cache(maxsize=1)
def load_page_catalog_schema() -> dict[str, object]:
    return json.loads(
        (ROOT / "research/schemas/page-catalog.schema.json").read_text(
            encoding="utf-8"
        )
    )


def validate_catalogs(data: object, evidence_ids: set[str]) -> list[str]:
    """Validate arbitrary catalog data without raising on malformed containers."""
    errors = validate_against_schema(
        data, load_page_catalog_schema(), "catalog"
    )
    if errors:
        return errors

    assert isinstance(data, dict)
    seen_slugs: set[str] = set()
    seen_orders: set[int] = set()
    for page_index, page in enumerate(data["pages"]):
        prefix = f"catalog.pages[{page_index}]"
        if page["slug"] in seen_slugs:
            errors.append(f"{prefix}.slug: duplicate {page['slug']}")
        if page["order"] in seen_orders:
            errors.append(f"{prefix}.order: duplicate {page['order']}")
        seen_slugs.add(page["slug"])
        seen_orders.add(page["order"])

        section_ids = [section["id"] for section in page["sections"]]
        if len(section_ids) != len(set(section_ids)):
            errors.append(f"{prefix}.sections: duplicate id")
        for section in page["sections"]:
            for block in section["blocks"]:
                if block["type"] == "table":
                    for row in block["rows"]:
                        if len(row) != len(block["headers"]):
                            errors.append(
                                f"{prefix}#{section['id']}: row width "
                                f"{len(row)} expected {len(block['headers'])}"
                            )
                references = list(block.get("evidence_ids", []))
                references.extend(
                    evidence_id
                    for item in block.get("items", [])
                    for evidence_id in item.get("evidence_ids", [])
                )
                for evidence_id in references:
                    if evidence_id not in evidence_ids:
                        errors.append(
                            f"{prefix}#{section['id']}: unknown evidence "
                            f"{evidence_id}"
                        )
    return errors


def load_page_catalogs(paths: list[Path]) -> list[dict[str, object]]:
    evidence = load_all_evidence()
    pages: list[dict[str, object]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_catalogs(data, set(evidence))
        if errors:
            raise ValueError(
                "\n".join(
                    f"{path.as_posix()}: {error}" for error in errors
                )
            )
        pages.extend(data["pages"])
    combined = {"schema_version": 1, "pages": pages}
    errors = validate_catalogs(combined, set(evidence))
    if errors:
        raise ValueError("\n".join(errors))
    return sorted(pages, key=lambda page: page["order"])


def relative_href(from_slug: str, to_slug: str) -> str:
    return posixpath.relpath(
        to_slug, posixpath.dirname(from_slug) or "."
    )


def decision_href(from_slug: str, decision_ref: str) -> str:
    if decision_ref not in DECISION_REFS:
        raise ValueError(f"disallowed decision ref {decision_ref}")
    return relative_href(from_slug, f"../{decision_ref}")


def load_all_indexes(
    root: Path = ROOT,
) -> dict[str, dict[str, object]]:
    registry = load_snapshot_registry(root / "research/source-snapshots.json")
    return {
        snapshot_id: json.loads(
            (root / "research/indexes" / f"{snapshot_id}.json").read_text(
                encoding="utf-8"
            )
        )
        for snapshot_id in sorted(registry)
    }


def load_all_evidence(root: Path = ROOT) -> dict[str, Evidence]:
    evidence = load_evidence(root / "research/target-evidence.json")
    reference = load_reference_evidence(root / "research/reference-evidence.json")
    duplicate = set(evidence) & set(reference)
    if duplicate:
        raise ValueError(f"duplicate evidence IDs: {sorted(duplicate)}")
    return {**evidence, **reference}


def _anchor(kind: str, snapshot_id: str, identity: str) -> str:
    raw = f"{kind}\0{snapshot_id}\0{identity}".encode()
    return f"entry-{hashlib.sha256(raw).hexdigest()[:16]}"


def build_search_documents(pages, indexes) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for page in pages:
        docs.append(
            {
                "kind": "page",
                "title": page["title"],
                "summary": page["summary"],
                "headings": " ".join(
                    section["title"] for section in page["sections"]
                ),
                "href": page["slug"],
                "path": "",
                "qualname": "",
                "key": "",
            }
        )
    destinations = {
        "files": "indexes/source-files.html",
        "symbols": "indexes/symbols-configs.html",
        "configs": "indexes/symbols-configs.html",
    }
    for snapshot_id, index in indexes.items():
        for kind in ("files", "symbols", "configs"):
            for row in index[kind]:
                identity = row["path"] if kind == "files" else row["id"]
                docs.append(
                    {
                        "kind": kind[:-1],
                        "title": identity,
                        "summary": snapshot_id,
                        "headings": "",
                        "href": (
                            f"{destinations[kind]}#"
                            f"{_anchor(kind, snapshot_id, identity)}"
                        ),
                        "path": row.get("path", ""),
                        "qualname": row.get("qualname", ""),
                        "key": row.get("key", ""),
                    }
                )
    for doc in docs:
        doc["searchable"] = " ".join(
            doc[key]
            for key in (
                "title",
                "summary",
                "headings",
                "path",
                "qualname",
                "key",
            )
        ).casefold()
    return sorted(
        docs, key=lambda doc: (doc["kind"], doc["title"], doc["href"])
    )


def script_safe_json(data: object) -> str:
    def compact(value: object) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    encoded = (
        "[\n" + ",\n".join(compact(item) for item in data) + "\n]"
        if isinstance(data, list) and data
        else compact(data)
    )
    return (
        encoded
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _block_evidence_ids(block: dict[str, object]) -> Iterable[str]:
    yield from block.get("evidence_ids", [])
    for item in block.get("items", []):
        yield from item.get("evidence_ids", [])


def _fixed_index_url(snapshot, row: dict[str, object], dataset: str) -> str:
    template = snapshot.blob_url_template
    if dataset == "files":
        if row["kind"] == "binary":
            return template.split("#", 1)[0].format(path=row["path"])
        start_line = 1
        end_line = max(1, row["line_count"])
    elif dataset == "symbols":
        start_line = row["line"]
        end_line = row["end_line"]
    else:
        start_line = row["line"]
        end_line = row["line"]
    return template.format(
        path=row["path"], start=start_line, end=end_line
    )


def _fixed_link_attributes(
    snapshot_id: str,
    source_path: str,
    *,
    start_line: int | None = None,
    end_line: int | None = None,
    file_only: bool = False,
) -> str:
    attributes = [
        'data-fixed-source-link="true"',
        f'data-snapshot-id="{_escape(snapshot_id)}"',
        f'data-source-path="{_escape(source_path)}"',
    ]
    if file_only:
        attributes.append('data-file-only="true"')
    else:
        attributes.extend(
            (
                f'data-start-line="{start_line}"',
                f'data-end-line="{end_line}"',
            )
        )
    return " ".join(attributes)


def _render_table(block: dict[str, object], section_id: str) -> str:
    headers = block["headers"]
    rows = block["rows"]
    for row in rows:
        if len(row) != len(headers):
            raise ValueError(
                f"table {section_id}: row width {len(row)} expected {len(headers)}"
            )
    head = "".join(f"<th scope=\"col\">{_escape(cell)}</th>" for cell in headers)
    tag_coverage_paths = (
        section_id == "target-coverage" and headers[0] == "path"
    )
    rendered_rows = []
    for row in rows:
        attributes = (
            f' data-coverage-path="{_escape(row[0])}"'
            if tag_coverage_paths
            else ""
        )
        cells = "".join(f"<td>{_escape(cell)}</td>" for cell in row)
        rendered_rows.append(f"<tr{attributes}>{cells}</tr>")
    body = ("\n" if tag_coverage_paths else "").join(rendered_rows)
    return (
        '<div class="table-scroll" tabindex="0" role="region" '
        'aria-label="可横向滚动的数据表"><table class="contract-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def _render_index_table(
    dataset: str,
    indexes: dict[str, dict[str, object]],
    registry,
) -> str:
    headers = {
        "files": ("snapshot", "kind", "path", "bytes", "sha256", "fixed link"),
        "symbols": (
            "snapshot",
            "qualname",
            "kind",
            "path",
            "line",
            "fixed link",
        ),
        "configs": (
            "snapshot",
            "key",
            "owner",
            "kind",
            "path",
            "line",
            "fixed link",
        ),
    }[dataset]
    head = "".join(f"<th scope=\"col\">{_escape(cell)}</th>" for cell in headers)
    rows: list[str] = []
    for snapshot_id, index in indexes.items():
        for row in index[dataset]:
            identity = row["path"] if dataset == "files" else row["id"]
            anchor = _anchor(dataset, snapshot_id, identity)
            empty_text = (
                dataset == "files"
                and row["kind"] != "binary"
                and row["line_count"] == 0
            )
            if empty_text:
                fixed_link = '<span class="file-empty">空文件（无行号）</span>'
            elif dataset == "files":
                file_only = row["kind"] == "binary"
                start_line = None if file_only else 1
                end_line = None if file_only else row["line_count"]
            elif dataset == "symbols":
                file_only = False
                start_line = row["line"]
                end_line = row["end_line"]
            else:
                file_only = False
                start_line = row["line"]
                end_line = row["line"]
            if not empty_text:
                url = _fixed_index_url(registry[snapshot_id], row, dataset)
                link_attributes = _fixed_link_attributes(
                    snapshot_id,
                    row["path"],
                    start_line=start_line,
                    end_line=end_line,
                    file_only=file_only,
                )
                fixed_link = (
                    f'<a class="print-url" {link_attributes} '
                    f'href="{_escape(url)}">固定版本 ↗</a>'
                )
            if dataset == "files":
                cells = (
                    snapshot_id,
                    row["kind"],
                    row["path"],
                    row["bytes"],
                    row["sha256"],
                )
            elif dataset == "symbols":
                cells = (
                    snapshot_id,
                    row["qualname"],
                    row["kind"],
                    row["path"],
                    f"{row['line']}–{row['end_line']}",
                )
            else:
                cells = (
                    snapshot_id,
                    row["key"],
                    row["owner"],
                    row["kind"],
                    row["path"],
                    row["line"],
                )
            rendered_cells = "".join(
                f"<td>{_escape(cell)}</td>" for cell in cells
            )
            rows.append(
                f'<tr id="{_escape(anchor)}">{rendered_cells}'
                f"<td>{fixed_link}</td></tr>"
            )
    rendered_rows = "\n".join(rows)
    return (
        '<div class="table-scroll" tabindex="0" role="region" '
        'aria-label="可横向滚动的数据表"><table class="index-table">'
        f"<thead><tr>{head}</tr></thead><tbody>{rendered_rows}</tbody></table></div>"
    )


def _render_block(
    block: dict[str, object],
    section_id: str,
    indexes: dict[str, dict[str, object]] | None,
    registry,
) -> str:
    block_type = block.get("type")
    if block_type == "paragraph":
        state = block["state"]
        label = STATE_LABELS.get(state, state)
        return (
            f'<p><span class="evidence-state" data-state="{_escape(state)}">'
            f"状态：{_escape(label)}</span> {_escape(block['text'])}</p>"
        )
    if block_type == "call_chain":
        items = []
        for item in block["items"]:
            items.append(
                '<div class="call-step">'
                f"<strong>{_escape(item['label'])}</strong>"
                f"<code>{_escape(item['path'])}</code>"
                f"<span>{_escape(item['symbol'])}</span>"
                "</div>"
            )
        return '<div class="call-chain" aria-label="学习调用链">' + '<span aria-hidden="true">→</span>'.join(items) + "</div>"
    if block_type == "table":
        return _render_table(block, section_id)
    if block_type == "source_refs":
        links = "".join(
            f'<li><a href="#evidence-{_escape(evidence_id)}">'
            f"证据 {_escape(evidence_id)}</a></li>"
            for evidence_id in block["evidence_ids"]
        )
        return f'<ul class="source-refs">{links}</ul>'
    if block_type == "index_table":
        if indexes is None:
            indexes = load_all_indexes()
        return _render_index_table(block["dataset"], indexes, registry)
    raise ValueError(f"block {block_type}: unsupported")


def _render_evidence_card(
    page_slug: str,
    evidence_id: str,
    row: Evidence,
    registry,
) -> str:
    state = STATE_LABELS.get(row.state, row.state)
    parts = [
        f'<section id="evidence-{_escape(evidence_id)}" class="rail-card evidence-card" data-rail-card>',
        f"<h2>{_escape(evidence_id)}</h2>",
        f'<p data-rail-content><span class="evidence-state" data-state="{_escape(row.state)}" data-evidence-state="{_escape(row.state)}">状态：{_escape(state)}</span></p>',
        f"<p data-rail-content>{_escape(row.claim)}</p>",
    ]
    if row.quote:
        parts.append(f"<p data-rail-content>摘录：{_escape(row.quote)}</p>")
    source_url = fixed_url(row, registry)
    if source_url:
        line_text = (
            "binary / 无行号"
            if row.start_line is None
            else f"L{row.start_line}–L{row.end_line}"
        )
        link_attributes = _fixed_link_attributes(
            row.snapshot_id,
            row.path,
            start_line=row.start_line,
            end_line=row.end_line,
            file_only=row.start_line is None,
        )
        parts.append(
            f'<a data-rail-content class="citation-link print-url" '
            f'{link_attributes} href="{_escape(source_url)}">'
            f"固定源码 {_escape(row.path)} · {_escape(line_text)} ↗</a>"
        )
    for source_id in row.source_ids:
        parts.append(
            f'<span data-rail-content class="citation-label">'
            f"来源台账 {_escape(source_id)}</span>"
        )
    for decision_ref in row.decision_refs:
        parts.append(
            f'<a data-rail-content class="citation-link print-url" href="{_escape(decision_href(page_slug, decision_ref))}">'
            f"决策记录 {_escape(decision_ref)}</a>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def render_page(page, navigation, evidence, search_documents) -> str:
    """Render one page using the shared three-column shell."""
    page_slug = page["slug"]
    referenced: list[str] = []
    for section in page["sections"]:
        for block in section["blocks"]:
            block_type = block.get("type")
            if block_type not in {
                "paragraph",
                "call_chain",
                "table",
                "source_refs",
                "index_table",
            }:
                raise ValueError(f"block {block_type}: unsupported")
            if block_type == "table":
                for row in block["rows"]:
                    if len(row) != len(block["headers"]):
                        raise ValueError(
                            f"table {section['id']}: row width {len(row)} "
                            f"expected {len(block['headers'])}"
                        )
            for evidence_id in _block_evidence_ids(block):
                if evidence_id not in evidence:
                    raise ValueError(
                        f"page {page_slug}#{section['id']}: unknown evidence "
                        f"{evidence_id}"
                    )
                if evidence_id not in referenced:
                    referenced.append(evidence_id)

    css_theme = relative_href(page_slug, "assets/theme.css")
    css_layout = relative_href(page_slug, "assets/layout.css")
    js_href = relative_href(page_slug, "assets/app.js")
    search_href = relative_href(page_slug, "search.html")
    home_href = relative_href(page_slug, "index.html")

    ordered = tuple(sorted(navigation, key=lambda row: row["order"]))
    nav_items = []
    for track in NAVIGATION_TRACKS:
        nav_items.append(
            f'<li class="chapter-group"><h2 class="chapter-group-label">'
            f"{_escape(track)}</h2></li>"
        )
        for item in ordered:
            if item["track"] != track:
                continue
            current = item["slug"] == page_slug
            attrs = ' class="active" aria-current="page"' if current else ""
            nav_items.append(
                f'<li><a data-page-link{attrs} '
                f'href="{_escape(relative_href(page_slug, item["slug"]))}">'
                f"{_escape(item['order'])} · {_escape(item['title'])}</a></li>"
            )

    objectives = "".join(
        f"<li>{_escape(item)}</li>" for item in page["objectives"]
    )
    prerequisites = "".join(
        f"<li>{_escape(item)}</li>" for item in page["prerequisites"]
    )
    toc = "".join(
        f'<a data-rail-content href="#{_escape(section["id"])}">'
        f"{_escape(section['title'])}</a>"
        for section in page["sections"]
    )

    registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
    source_example = ""
    if page_slug == "index.html":
        snapshot_id = "qwen3-tts-022e286b"
        source_path = "qwen_tts/inference/qwen3_tts_model.py"
        start_line, end_line = 83, 87
        source_url = registry[snapshot_id].blob_url_template.format(
            path=source_path, start=start_line, end=end_line
        )
        link_attributes = _fixed_link_attributes(
            snapshot_id,
            source_path,
            start_line=start_line,
            end_line=end_line,
        )
        excerpt = (
            "    def from_pretrained(\n"
            "        cls,\n"
            "        pretrained_model_name_or_path: str,\n"
            "        **kwargs,\n"
            '    ) -> "Qwen3TTSModel":'
        )
        source_example = (
            '<div class="source-example" id="source">'
            '<div class="code-header"><span>官方装载入口（短摘录）</span>'
            '<div class="code-actions">'
            f'<a class="source-link print-url" {link_attributes} '
            f'href="{_escape(source_url)}">固定源码 L83–L87 ↗</a>'
            '<button class="copy-source" type="button" '
            'data-copy-target="qwen-load-example">复制</button>'
            '<span class="copy-status" role="status" aria-live="polite"></span>'
            '</div></div>'
            f'<pre id="qwen-load-example"><code>{_escape(excerpt)}</code></pre>'
            '</div>'
        )
    indexes = None
    if any(
        block["type"] == "index_table"
        for section in page["sections"]
        for block in section["blocks"]
    ):
        indexes = load_all_indexes()

    sections: list[str] = []
    for section in page["sections"]:
        blocks = "".join(
            _render_block(block, section["id"], indexes, registry)
            for block in section["blocks"]
        )
        if page_slug == "search.html" and section["id"] == "search-results":
            blocks += (
                '<p id="search-results-status" role="status" aria-live="polite">请输入关键词</p>'
                '<div class="search-results"></div>'
            )
        if page_slug == "search.html" and section["id"] == "no-script-index":
            directory = "".join(
                f'<li><a href="{_escape(relative_href(page_slug, item["slug"]))}">'
                f"{_escape(item['title'])}</a></li>"
                for item in sorted(
                    ordered, key=lambda row: (row["title"].casefold(), row["slug"])
                )
            )
            blocks += f'<ul class="alphabetic-directory">{directory}</ul>'
        sections.append(
            f'<section id="{_escape(section["id"])}"><h2>'
            f"{_escape(section['title'])}</h2>{blocks}</section>"
        )

    page_nav = ""
    page_position = next(
        (index for index, item in enumerate(ordered) if item["slug"] == page_slug),
        None,
    )
    if page_position is not None:
        adjacent = []
        if page_position > 0:
            previous = ordered[page_position - 1]
            adjacent.append(
                f'<a rel="prev" href="{_escape(relative_href(page_slug, previous["slug"]))}">'
                f"← 上一页：{_escape(previous['title'])}</a>"
            )
        if page_position + 1 < len(ordered):
            following = ordered[page_position + 1]
            adjacent.append(
                f'<a rel="next" href="{_escape(relative_href(page_slug, following["slug"]))}">'
                f"下一页：{_escape(following['title'])} →</a>"
            )
        if adjacent:
            page_nav = (
                '<nav class="page-nav" aria-label="相邻章节">'
                + "".join(adjacent)
                + "</nav>"
            )
    if page.get("next_slug"):
        next_slug = page["next_slug"]
        page_nav += (
            '<nav class="page-nav route-next" aria-label="下一步学习">'
            f'<a rel="next" href="{_escape(relative_href(page_slug, next_slug))}">'
            '下一页：进入实施前的证据复查 →</a></nav>'
        )

    evidence_cards = "".join(
        _render_evidence_card(page_slug, evidence_id, evidence[evidence_id], registry)
        for evidence_id in referenced
    )
    search_data = ""
    if page_slug == "search.html":
        search_data = (
            '  <script id="search-data" type="application/json">'
            f"{script_safe_json(search_documents)}</script>\n"
        )
    rendered_sections = "\n".join(sections)

    rendered = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{_escape(page['summary'])}">
  <title>{_escape(page['title'])} · Qwen3-TTS × Ascend 910B</title>
  <link rel="stylesheet" href="{_escape(css_theme)}">
  <link rel="stylesheet" href="{_escape(css_layout)}">
</head>
<body id="top">
  <header class="site-header">
    <a class="brand" href="{_escape(home_href)}">Qwen3-TTS × Ascend <small>Migration Field Notes</small></a>
    <div class="mobile-chapter-title" aria-label="当前章节">{_escape(page['title'])}</div>
    <form id="site-search" class="search" role="search" action="{_escape(search_href)}" method="get">
      <label><span class="sr-only">站内搜索</span><input name="q" type="search" aria-label="站内搜索" placeholder="搜索文件、类、配置项、证据编号"></label>
      <button class="search-submit" type="submit">搜索</button>
    </form>
    <noscript><a class="search-fallback" href="#chapter-tree">无脚本模式：浏览章节索引</a></noscript>
    <button class="search-enhancement" type="button" aria-controls="site-search" aria-expanded="false" aria-label="打开站内搜索">⌕</button>
    <div class="revision">四个固定快照 · 静态知识站</div>
  </header>
  <div class="site-shell">
    <div class="sidebar-controls">
      <button id="toggle-left" class="sidebar-toggle left-toggle" type="button" aria-controls="chapter-nav" aria-expanded="true" aria-label="收起章节导航">‹</button>
      <button id="toggle-right" class="sidebar-toggle right-toggle" type="button" aria-controls="evidence-rail" aria-expanded="true" aria-label="收起证据栏">›</button>
    </div>
    <nav id="chapter-nav" class="chapter-nav" aria-label="章节导航">
      <div class="rail-icons" role="group" aria-label="章节快捷入口"><a class="rail-link" href="#top"><span aria-hidden="true">⌂</span><span class="rail-tooltip">首页</span></a><a class="rail-link" href="#chapter-tree"><span aria-hidden="true">▤</span><span class="rail-tooltip">章节</span></a></div>
      <div class="sidebar-content"><p class="nav-label">学习路径</p><ul id="chapter-tree" class="chapter-tree">{''.join(nav_items)}</ul></div>
      <button class="drawer-close" type="button" data-close-drawer="left">关闭章节导航</button>
    </nav>
    <main id="article-content">
      <article>
        <p class="breadcrumb">{_escape(page['group'])} / {_escape(page['order'])}</p>
        <p class="lesson-wayfinding">学习轨道：{_escape(page['track'])}</p>
        <h1>{_escape(page['title'])}</h1>
        <p class="lead">{_escape(page['summary'])}</p>
        <div class="learning-contract"><div><h2>学习目标</h2><ul>{objectives}</ul></div><div><h2>前置知识</h2><ul>{prerequisites}</ul></div></div>
        <div class="status-grid" aria-label="证据状态图例"><span class="evidence-state" data-state="verified">已核验</span><span class="evidence-state" data-state="project_claim">项目声明</span><span class="evidence-state" data-state="inference">静态推断</span><span class="evidence-state" data-state="pending_hardware">待真机验证</span></div>
{source_example}
        {rendered_sections}
        {page_nav}
      </article>
    </main>
    <aside id="evidence-rail" class="evidence-rail" aria-label="证据与页内目录">
      <div class="rail-icons" role="group" aria-label="证据快捷入口"><a class="rail-link" data-rail-target="page-toc" href="#page-toc"><span aria-hidden="true">§</span><span class="rail-tooltip">目录</span></a></div>
      <div class="sidebar-content"><section id="page-toc" class="rail-card toc-card" data-rail-card><h2>本页目录</h2>{toc}</section>{evidence_cards}</div>
      <button class="drawer-close" type="button" data-close-drawer="right">关闭证据栏</button>
    </aside>
  </div>
  <div class="drawer-backdrop" hidden></div>
  <footer class="site-footer"><p>Qwen3-TTS × Ascend 910B 学习站 · 源码引用固定版本，迁移结论需以真机复验为准。</p></footer>
{search_data}  <script type="module" src="{_escape(js_href)}"></script>
</body>
</html>"""
    return rendered.rstrip("\n") + "\n"


def build_site(output_root: Path, catalog_paths: list[Path]) -> list[Path]:
    pages = load_page_catalogs(catalog_paths)
    navigation = tuple(sorted(pages, key=lambda page: page["order"]))
    documents = build_search_documents(pages, load_all_indexes())
    evidence = load_all_evidence()
    written: list[Path] = []
    for page in navigation:
        target = output_root / page["slug"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_page(page, navigation, evidence, documents), encoding="utf-8"
        )
        written.append(target)
    search_path = output_root / "assets/search-index.json"
    search_path.parent.mkdir(parents=True, exist_ok=True)
    search_path.write_text(
        json.dumps(
            documents, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(search_path)
    return written
