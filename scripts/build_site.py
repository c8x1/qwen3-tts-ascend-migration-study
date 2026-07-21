#!/usr/bin/env python3
"""Build the static knowledge site from page catalogs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.site_builder import build_site  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "site",
        help="output site directory",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        action="append",
        help="page catalog (repeat for multiple catalogs)",
    )
    return parser.parse_args()


def default_catalogs() -> list[Path]:
    candidates = [
        ROOT / "content/site-foundation.json",
        ROOT / "content/target-architecture.json",
        ROOT / "content/target-training.json",
        ROOT / "content/reference-mindspeed-mm.json",
        ROOT / "content/reference-mindspeed-llm.json",
        ROOT / "content/reference-moss-tts.json",
        ROOT / "content/migration-mapping.json",
    ]
    return [path for path in candidates if path.is_file()]


def main() -> int:
    args = parse_args()
    catalogs = args.catalog or default_catalogs()
    written = build_site(args.output, catalogs)
    pages = [path for path in written if path.suffix == ".html"]
    search_path = args.output / "assets/search-index.json"
    documents = json.loads(search_path.read_text(encoding="utf-8"))
    print(f"built {len(pages)} pages and {len(documents)} search documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
