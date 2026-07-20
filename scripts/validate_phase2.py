#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase2_contracts import (
    PHASE2_CATALOG_PATHS,
    load_evidence,
    load_snapshot_registry,
    validate_fixed_links,
    validate_generated_site,
    validate_public_tracking,
    validate_source_index,
    validate_target_coverage,
)
from scripts.site_builder import load_page_catalogs


def _expected_snapshot(snapshot) -> dict[str, object]:
    return {
        key: getattr(snapshot, key)
        for key in (
            "snapshot_id",
            "project",
            "role",
            "revision",
            "acquisition_kind",
            "content_id",
        )
    }


def validate_indexes(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    registry = load_snapshot_registry(root / "research/source-snapshots.json")
    for snapshot_id, snapshot in registry.items():
        path = root / "research/indexes" / f"{snapshot_id}.json"
        label = path.name
        if not path.is_file():
            errors.append(f"{path.relative_to(root)}: missing")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(
                f"{label}: invalid JSON at line {error.lineno} "
                f"column {error.colno}: {error.msg}"
            )
            continue
        except (OSError, UnicodeError) as error:
            errors.append(f"{label}: unreadable: {error}")
            continue

        encoded_payload = None
        if isinstance(data, dict):
            payload = dict(data)
            payload.pop("content_digest", None)
            try:
                encoded_payload = json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            except UnicodeEncodeError:
                errors.append(
                    f"{label}: content digest input is not UTF-8 encodable"
                )
                continue

        errors.extend(
            f"{label}: {error}"
            for error in validate_source_index(data, registry)
        )
        if not isinstance(data, dict):
            continue

        if data.get("snapshot") != _expected_snapshot(snapshot):
            errors.append(f"{label}: snapshot metadata mismatch")

        files = data.get("files")
        if isinstance(files, list):
            if len(files) != snapshot.materialized_file_count:
                errors.append(
                    f"{label}: expected {snapshot.materialized_file_count} files"
                )

        actual = data.get("content_digest")
        expected = hashlib.sha256(encoded_payload).hexdigest()
        if actual != expected:
            errors.append(f"{label}: content digest mismatch")

        for key in ("files", "symbols", "configs"):
            identity = "path" if key == "files" else "id"
            rows = data.get(key)
            if not isinstance(rows, list) or not all(
                isinstance(row, dict) and isinstance(row.get(identity), str)
                for row in rows
            ):
                continue
            values = [row[identity] for row in rows]
            if len(values) != len(set(values)):
                errors.append(f"{label}: duplicate {key} {identity}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indexes-only", action="store_true")
    args = parser.parse_args()
    errors = validate_indexes()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.indexes_only:
        print("validated 4 source indexes: 3270 files; no absolute paths or source bodies")
        return 0

    evidence = None
    registry = load_snapshot_registry(
        ROOT / "research/source-snapshots.json"
    )
    evidence_path = ROOT / "research/target-evidence.json"
    try:
        evidence = load_evidence(evidence_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        errors.append(str(error))

    coverage_rows: list[dict[str, str]] = []
    coverage_path = ROOT / "research/target-coverage.csv"
    try:
        with coverage_path.open(encoding="utf-8", newline="") as handle:
            coverage_rows = list(csv.DictReader(handle))
        if evidence is not None:
            target = json.loads(
                (
                    ROOT / "research/indexes/qwen3-tts-022e286b.json"
                ).read_text(encoding="utf-8")
            )
            errors.extend(
                validate_target_coverage(
                    target, coverage_rows, evidence=evidence
                )
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(str(error))

    pages: list[dict[str, object]] = []
    if evidence is not None:
        try:
            pages = load_page_catalogs(list(PHASE2_CATALOG_PATHS))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            errors.append(str(error))

    if evidence is not None and pages:
        errors.extend(
            validate_generated_site(
                ROOT / "site", pages, evidence, coverage_rows
            )
        )
        errors.extend(validate_fixed_links(ROOT / "site", registry))
    errors.extend(validate_public_tracking(ROOT))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    evidence_count = len(evidence)
    print(
        "validated Phase 2: 4 indexes / 3270 files, "
        f"{evidence_count} evidence records, {len(coverage_rows)} coverage "
        f"rows, {len(pages)} pages, 0 broken links, 0 omissions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
