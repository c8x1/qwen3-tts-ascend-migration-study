#!/usr/bin/env python3
"""Fail-closed publication validation for the Phase 3 static site."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_site import default_catalogs
from scripts.phase2_contracts import (
    load_evidence,
    validate_public_tracking,
    validate_target_coverage,
)
from scripts.phase3_contracts import load_reference_evidence, validate_reference_coverage
from scripts.site_builder import build_site, load_all_indexes, load_page_catalogs
from scripts.validate_phase2 import validate_indexes


def main() -> int:
    errors = validate_indexes(ROOT)
    try:
        indexes = load_all_indexes(ROOT)
        target_evidence = load_evidence(ROOT / "research/target-evidence.json")
        reference_evidence = load_reference_evidence(ROOT / "research/reference-evidence.json")
        coverage_path = ROOT / "research/reference-coverage.csv"
        errors.extend(validate_reference_coverage(
            coverage_path, {key: {} for key in reference_evidence}, reference_evidence
        ))
        with (ROOT / "research/target-coverage.csv").open(encoding="utf-8", newline="") as handle:
            target_rows = list(csv.DictReader(handle))
        errors.extend(validate_target_coverage(indexes["qwen3-tts-022e286b"], ROOT / "research/target-coverage.csv", target_evidence))
        pages = load_page_catalogs(default_catalogs())
        build_site(ROOT / "site", default_catalogs())
        expected = {page["slug"] for page in pages}
        actual = {path.relative_to(ROOT / "site").as_posix() for path in (ROOT / "site").rglob("*.html")}
        errors.extend(f"site: missing {slug}" for slug in sorted(expected - actual))
        errors.extend(validate_public_tracking(ROOT))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, csv.Error) as error:
        errors.append(f"phase3 validation: {error}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated Phase 3: {len(indexes)} indexes / {len(reference_evidence)} reference evidence / {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
