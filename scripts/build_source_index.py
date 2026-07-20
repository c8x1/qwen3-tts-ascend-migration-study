#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase2_contracts import load_snapshot_registry, validate_source_index
from scripts.source_index import build_index, write_canonical_json


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
