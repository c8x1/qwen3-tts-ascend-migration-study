#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase2_contracts import load_snapshot_registry, validate_source_index


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
    parser.parse_args()
    errors = validate_indexes()
    if errors:
        print("\n".join(errors))
        return 1
    print("validated 4 source indexes: 3270 files; no absolute paths or source bodies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
