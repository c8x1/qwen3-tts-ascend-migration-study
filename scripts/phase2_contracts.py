"""Contracts for immutable source snapshots and generated source indexes."""

from __future__ import annotations

import collections
import csv
import hashlib
import os
import json
import re
import subprocess
import tempfile
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache, lru_cache
from html.parser import HTMLParser
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


_ROOT = Path(__file__).resolve().parents[1]
ROOT = _ROOT
_SOURCE_INDEX_SCHEMA = _ROOT / "research" / "schemas" / "source-index.schema.json"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_FORBIDDEN_KEYS = {
    "source_root",
    "body",
    "source",
    "text",
    "generated_at",
    "local_path",
}


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


DECISION_REFS = {
    "research/reference-selection-proposal.md",
    "research/selected-revisions.csv",
}
EVIDENCE_STATES = {"verified", "project_claim", "inference", "pending_hardware"}
DISPOSITIONS = {"mapped", "excluded", "pending"}
COVERAGE_FIELDS = (
    "path",
    "disposition",
    "page",
    "section",
    "evidence_ids",
    "reason",
)
PHASE2_CATALOG_PATHS = (
    ROOT / "content/site-foundation.json",
    ROOT / "content/target-architecture.json",
    ROOT / "content/target-training.json",
)


_APPROVED: dict[str, dict[str, Any]] = {
    "qwen3-tts-022e286b": {
        "snapshot_id": "qwen3-tts-022e286b",
        "project": "QwenLM/Qwen3-TTS",
        "role": "official-target",
        "revision": "022e286b98fbec7e1e916cb940cdf532cd9f488e",
        "acquisition_kind": "git-sparse-checkout",
        "content_id": "git-tree:33e4644dc5a698874fa035630d1878aa453b564c",
        "materialized_file_count": 35,
        "source_url": "https://github.com/QwenLM/Qwen3-TTS",
        "blob_url_template": "https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/{path}#L{start}-L{end}",
        "excluded": {
            "paths": [".github/.DS_Store", "assets/Qwen3_TTS.pdf"],
            "reason": "sparse source-only checkout excludes rendered paper and macOS metadata",
        },
        "gitlinks": [],
    },
    "mindspeed-mm-0edd553e": {
        "snapshot_id": "mindspeed-mm-0edd553e",
        "project": "Ascend/MindSpeed-MM",
        "role": "main-reference",
        "revision": "0edd553e0ac9c912fe422c42cc9f42db9255ddcf",
        "acquisition_kind": "codeload-archive",
        "content_id": "archive-sha256:1b52f9a6a8e3536f02a7a06ed01cc4d00dafc57617783ca2a04d0250b670ba15",
        "materialized_file_count": 1405,
        "source_url": "https://gitcode.com/Ascend/MindSpeed-MM",
        "blob_url_template": "https://github.com/Ascend/MindSpeed-MM/blob/0edd553e0ac9c912fe422c42cc9f42db9255ddcf/{path}#L{start}-L{end}",
        "excluded": {
            "paths": [],
            "reason": "exact-SHA codeload tree; no Git metadata retained",
        },
        "gitlinks": [],
    },
    "mindspeed-llm-434baff7": {
        "snapshot_id": "mindspeed-llm-434baff7",
        "project": "Ascend/MindSpeed-LLM",
        "role": "scale-satellite",
        "revision": "434baff794bd5594ebc9ed8a5b399110da9a44f0",
        "acquisition_kind": "codeload-archive",
        "content_id": "git-tree:a00c5d3bc01d3357a9c943fef923571b5df676e2",
        "materialized_file_count": 1664,
        "source_url": "https://gitcode.com/Ascend/MindSpeed-LLM",
        "blob_url_template": "https://github.com/Ascend/MindSpeed-LLM/blob/434baff794bd5594ebc9ed8a5b399110da9a44f0/{path}#L{start}-L{end}",
        "excluded": {
            "paths": [],
            "reason": "tree-hash-verified exact-SHA codeload tree; no Git metadata retained",
        },
        "gitlinks": [],
    },
    "moss-tts-ad99ec5f": {
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
                "assets/audio/reference_02_s1.wav",
                "assets/audio/reference_02_s2.wav",
                "assets/audio/reference_en.m4a",
                "assets/audio/reference_en_0.mp3",
                "assets/audio/reference_en_1.mp3",
                "assets/audio/reference_en_2.mp3",
                "assets/audio/reference_en_3.mp3",
                "assets/audio/reference_zh.wav",
                "assets/audio/reference_zh_0.wav",
                "assets/audio/reference_zh_1.wav",
                "assets/audio/reference_zh_2.wav",
                "assets/audio/reference_zh_3.mp3",
                "assets/text/moss_tts_example_texts.jsonl",
                "assets/text/moss_voice_generator_example_texts.jsonl",
                "moss_tts_realtime/audio/prompt_audio.mp3",
                "moss_tts_realtime/audio/prompt_audio1.mp3",
                "moss_tts_realtime/audio/user1.wav",
                "moss_tts_realtime/audio/user2.wav",
            ],
            "reason": "source-only sparse checkout excludes committed wav/mp3/m4a/jsonl assets",
        },
        "gitlinks": [
            {
                "path": "moss_audio_tokenizer",
                "revision": "56776e867cb38446fa4bc00d0aceccab5001b008",
                "initialized": False,
            }
        ],
    },
}

_SNAPSHOT_FIELDS = {
    "snapshot_id",
    "project",
    "role",
    "revision",
    "acquisition_kind",
    "content_id",
    "materialized_file_count",
    "source_url",
    "blob_url_template",
    "excluded",
    "gitlinks",
}
_STRING_FIELDS = {
    "snapshot_id",
    "project",
    "role",
    "revision",
    "acquisition_kind",
    "content_id",
    "source_url",
    "blob_url_template",
}


def _relative_posix(path: object) -> bool:
    if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
        return False
    parts = path.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def _validate_exact_fields(
    value: dict[str, Any], allowed: set[str], path: str, errors: list[str]
) -> bool:
    for field in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {field}")
    for field in sorted(allowed - set(value)):
        errors.append(f"{path}: missing field {field}")
    return set(value) == allowed


def validate_snapshot_registry(data: object) -> list[str]:
    """Return deterministic validation errors for an arbitrary JSON value."""
    if not isinstance(data, dict):
        return ["registry: expected object"]

    errors: list[str] = []
    root_fields = {"schema_version", "snapshots"}
    _validate_exact_fields(data, root_fields, "registry", errors)

    version = data.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        errors.append("registry.schema_version: expected 1")

    rows = data.get("snapshots")
    if not isinstance(rows, list):
        errors.append("registry.snapshots: expected array")
        return errors

    seen_ids: set[str] = set()
    observed_ids: set[str] = set()
    for index, row in enumerate(rows):
        row_path = f"snapshots[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_path}: expected object")
            continue

        complete = _validate_exact_fields(row, _SNAPSHOT_FIELDS, row_path, errors)
        for field in sorted(_STRING_FIELDS & set(row)):
            if not isinstance(row[field], str) or not row[field]:
                errors.append(f"{row_path}.{field}: expected non-empty string")

        snapshot_id = row.get("snapshot_id")
        approved = _APPROVED.get(snapshot_id) if isinstance(snapshot_id, str) else None
        if isinstance(snapshot_id, str):
            if snapshot_id in seen_ids:
                errors.append(f"{row_path}.snapshot_id: duplicate {snapshot_id}")
            seen_ids.add(snapshot_id)
            observed_ids.add(snapshot_id)
            if approved is None:
                errors.append(f"{row_path}.snapshot_id: unapproved {snapshot_id}")

        revision = row.get("revision")
        if isinstance(revision, str) and not _HEX40.fullmatch(revision):
            errors.append(f"{row_path}.revision: expected 40 lowercase hex characters")

        count = row.get("materialized_file_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append(f"{row_path}.materialized_file_count: expected nonnegative integer")

        excluded = row.get("excluded")
        if not isinstance(excluded, dict):
            errors.append(f"{row_path}.excluded: expected object")
        else:
            _validate_exact_fields(excluded, {"paths", "reason"}, f"{row_path}.excluded", errors)
            paths = excluded.get("paths")
            if not isinstance(paths, list):
                errors.append(f"{row_path}.excluded.paths: expected array")
            else:
                seen_paths: set[str] = set()
                paths_path = f"{row_path}.excluded.paths"
                for excluded_path in paths:
                    if not _relative_posix(excluded_path):
                        errors.append(
                            f"{paths_path}: expected relative POSIX path {excluded_path}"
                        )
                    if isinstance(excluded_path, str):
                        if excluded_path in seen_paths:
                            errors.append(f"{paths_path}: duplicate path")
                        else:
                            seen_paths.add(excluded_path)
            if not isinstance(excluded.get("reason"), str) or not excluded.get("reason"):
                errors.append(f"{row_path}.excluded.reason: expected nonempty string")

        gitlinks = row.get("gitlinks")
        if not isinstance(gitlinks, list):
            errors.append(f"{row_path}.gitlinks: expected array")
        else:
            seen_gitlinks: set[str] = set()
            for link_index, link in enumerate(gitlinks):
                link_path = f"{row_path}.gitlinks[{link_index}]"
                if not isinstance(link, dict):
                    errors.append(f"{link_path}: expected object")
                    continue
                _validate_exact_fields(link, {"path", "revision", "initialized"}, link_path, errors)
                path_value = link.get("path")
                if not _relative_posix(path_value):
                    errors.append(f"{link_path}.path: expected relative POSIX path")
                elif path_value in seen_gitlinks:
                    errors.append(f"{link_path}.path: duplicate path {path_value}")
                else:
                    seen_gitlinks.add(path_value)
                link_revision = link.get("revision")
                if not isinstance(link_revision, str) or not _HEX40.fullmatch(link_revision):
                    errors.append(f"{link_path}.revision: expected 40 lowercase hex characters")
                if not isinstance(link.get("initialized"), bool):
                    errors.append(f"{link_path}.initialized: expected boolean")

        if approved is not None and complete:
            for field in sorted(_SNAPSHOT_FIELDS):
                if row.get(field) != approved[field]:
                    expected = approved[field]
                    if isinstance(expected, str):
                        errors.append(f"{row_path}.{field}: expected {expected}")
                    else:
                        errors.append(
                            f"{row_path}.{field}: does not match approved snapshot metadata"
                        )

    approved_ids = set(_APPROVED)
    if len(rows) != len(_APPROVED) or observed_ids != approved_ids:
        errors.append(f"registry.snapshots: expected approved IDs {sorted(approved_ids)}")
    return errors


def load_snapshot_registry(path: Path) -> dict[str, Snapshot]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_snapshot_registry(data)
    if errors:
        raise ValueError("invalid snapshot registry:\n" + "\n".join(errors))

    registry: dict[str, Snapshot] = {}
    for row in data["snapshots"]:
        registry[row["snapshot_id"]] = Snapshot(
            snapshot_id=row["snapshot_id"],
            project=row["project"],
            role=row["role"],
            revision=row["revision"],
            acquisition_kind=row["acquisition_kind"],
            content_id=row["content_id"],
            materialized_file_count=row["materialized_file_count"],
            blob_url_template=row["blob_url_template"],
            excluded_paths=tuple(row["excluded"]["paths"]),
            gitlinks=tuple(dict(link) for link in row["gitlinks"]),
        )
    return registry


@cache
def load_source_index_schema() -> dict[str, Any]:
    return json.loads(_SOURCE_INDEX_SCHEMA.read_text(encoding="utf-8"))


def _json_type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    return False


def _validate_schema(
    value: object,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
    one_of_error: str = "expected exactly one allowed shape",
) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _json_type_matches(value, expected_type):
        errors.append(f"{path}: expected {expected_type}")
        return
    if isinstance(expected_type, list) and not any(
        isinstance(candidate, str) and _json_type_matches(value, candidate)
        for candidate in expected_type
    ):
        errors.append(f"{path}: expected one of types {expected_type}")
        return

    if isinstance(value, dict):
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        required = schema.get("required")
        if isinstance(required, list):
            for field in sorted(item for item in required if isinstance(item, str)):
                if field not in value:
                    errors.append(f"{path}: missing field {field}")
        if schema.get("additionalProperties") is False:
            for field in sorted(set(value) - set(properties)):
                errors.append(f"{path}: unknown field {field}")
        for field in sorted(set(value) & set(properties)):
            child_schema = properties[field]
            if isinstance(child_schema, dict):
                child_path = f"{path}.{field}"
                _validate_schema(
                    value[field], child_schema, child_path, errors, one_of_error
                )

    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if isinstance(minimum_items, int) and len(value) < minimum_items:
            errors.append(f"{path}: fewer than {minimum_items} items")
        if schema.get("uniqueItems") is True:
            for index, item in enumerate(value):
                if any(item == previous for previous in value[:index]):
                    errors.append(f"{path}: duplicate item")
                    break
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(
                    item,
                    item_schema,
                    f"{path}[{index}]",
                    errors,
                    one_of_error,
                )

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']}")
    choices = schema.get("enum")
    if isinstance(choices, list) and value not in choices:
        errors.append(f"{path}: expected one of {choices}")
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str) and re.search(pattern, value) is None:
        errors.append(f"{path}: does not match pattern {pattern}")
    minimum_length = schema.get("minLength")
    if isinstance(minimum_length, int) and isinstance(value, str) and len(value) < minimum_length:
        errors.append(f"{path}: shorter than {minimum_length}")
    maximum_length = schema.get("maxLength")
    if isinstance(maximum_length, int) and isinstance(value, str) and len(value) > maximum_length:
        errors.append(f"{path}: longer than {maximum_length}")
    minimum = schema.get("minimum")
    if (
        isinstance(minimum, (int, float))
        and not isinstance(minimum, bool)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value < minimum
    ):
        errors.append(f"{path}: expected minimum {minimum}")

    variants = schema.get("oneOf")
    if isinstance(variants, list):
        matches = 0
        for variant in variants:
            variant_errors: list[str] = []
            if isinstance(variant, dict):
                _validate_schema(
                    value, variant, path, variant_errors, one_of_error
                )
            else:
                variant_errors.append(f"{path}: invalid schema variant")
            if not variant_errors:
                matches += 1
        if matches != 1:
            errors.append(f"{path}: {one_of_error}")


def validate_against_schema(
    data: object, schema: dict[str, object], path: str
) -> list[str]:
    errors: list[str] = []
    _validate_schema(
        data,
        schema,
        path,
        errors,
        "expected exactly one oneOf branch",
    )
    return errors


@lru_cache(maxsize=1)
def load_target_evidence_schema() -> dict[str, object]:
    return json.loads(
        (
            ROOT / "research/schemas/target-evidence.schema.json"
        ).read_text(encoding="utf-8")
    )


def _absolute_path(path: str) -> bool:
    return path.startswith("/") or path.startswith("\\\\") or bool(_WINDOWS_DRIVE.match(path))


def _walk_index_policy(value: object, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for field in sorted(value):
            if field in _FORBIDDEN_KEYS:
                errors.append(f"{path}: forbidden field {field}")
            _walk_index_policy(value[field], f"{path}.{field}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_index_policy(item, f"{path}[{index}]", errors)
    elif isinstance(value, str) and _absolute_path(value):
        errors.append(f"{path}: absolute path forbidden")


def _materialized_digest(data: object) -> str:
    materialized = dict(data) if isinstance(data, dict) else data
    if isinstance(materialized, dict):
        materialized.pop("content_digest", None)
    encoded = json.dumps(
        materialized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _check_index_path(path: str, label: str, errors: list[str]) -> None:
    if not _absolute_path(path) and not _relative_posix(path):
        errors.append(f"{label}: expected relative POSIX path")


def _check_sorted_unique(
    rows: list[dict[str, Any]], key: str, label: str, errors: list[str]
) -> None:
    values = [row[key] for row in rows]
    if values != sorted(values):
        errors.append(f"{label}: rows must be sorted by {key}")
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"{label}: duplicate {key} {value}")
        seen.add(value)


def validate_source_index(
    data: object, registry: dict[str, Snapshot]
) -> list[str]:
    """Validate one source index structurally and semantically without raising."""
    if not isinstance(data, dict):
        return ["index: expected object"]

    errors: list[str] = []
    _validate_schema(data, load_source_index_schema(), "index", errors)
    policy_errors: list[str] = []
    _walk_index_policy(data, "index", policy_errors)
    if errors:
        return errors + policy_errors
    errors.extend(policy_errors)

    snapshot_data = data["snapshot"]
    snapshot_id = snapshot_data["snapshot_id"]
    snapshot = registry.get(snapshot_id)
    if snapshot is None:
        errors.append(f"index.snapshot.snapshot_id: unknown snapshot {snapshot_id}")
    else:
        for field in (
            "snapshot_id",
            "project",
            "role",
            "revision",
            "acquisition_kind",
            "content_id",
        ):
            expected = getattr(snapshot, field)
            if snapshot_data[field] != expected:
                errors.append(f"index.snapshot.{field}: expected {expected}")

    files = data["files"]
    symbols = data["symbols"]
    configs = data["configs"]
    for index, row in enumerate(files):
        _check_index_path(row["path"], f"index.files[{index}].path", errors)
        if row["kind"] == "binary":
            if row["line_count"] is not None:
                errors.append(
                    f"index.files[{index}].line_count: binary files require null"
                )
        elif not isinstance(row["line_count"], int):
            errors.append(
                f"index.files[{index}].line_count: nonbinary files require an integer"
            )
    for label, rows in (("symbols", symbols), ("configs", configs)):
        for index, row in enumerate(rows):
            _check_index_path(row["path"], f"index.{label}[{index}].path", errors)

    _check_sorted_unique(files, "path", "index.files", errors)
    _check_sorted_unique(symbols, "id", "index.symbols", errors)
    _check_sorted_unique(configs, "id", "index.configs", errors)

    files_by_path: dict[str, dict[str, Any]] = {}
    for row in files:
        files_by_path.setdefault(row["path"], row)

    for index, row in enumerate(symbols):
        expected_id = f"{row['path']}:{row['qualname']}:{row['line']}"
        if row["id"] != expected_id:
            errors.append(f"index.symbols[{index}].id: expected {expected_id}")
        if row["line"] > row["end_line"]:
            errors.append(f"index.symbols[{index}]: line exceeds end_line")
        owner = files_by_path.get(row["path"])
        if owner is None:
            errors.append(f"index.symbols[{index}].path: not in files")
        elif owner["line_count"] is None:
            errors.append(
                f"index.symbols[{index}].line: exceeds file line_count"
            )
        else:
            if row["line"] > owner["line_count"]:
                errors.append(
                    f"index.symbols[{index}].line: exceeds file line_count"
                )
            if row["end_line"] > owner["line_count"]:
                errors.append(
                    f"index.symbols[{index}].end_line: exceeds file line_count"
                )

    for index, row in enumerate(configs):
        expected_id = f"{row['path']}:{row['key']}:{row['line']}"
        if row["id"] != expected_id:
            errors.append(f"index.configs[{index}].id: expected {expected_id}")
        owner = files_by_path.get(row["path"])
        if owner is None:
            errors.append(f"index.configs[{index}].path: not in files")
        elif owner["line_count"] is None:
            errors.append(
                f"index.configs[{index}].line: exceeds file line_count"
            )
        elif row["line"] > owner["line_count"]:
            errors.append(
                f"index.configs[{index}].line: exceeds file line_count"
            )

    if data["content_digest"] != _materialized_digest(data):
        errors.append("index.content_digest: does not match materialized content")
    return errors


def validate_evidence(
    data: object,
    registry: dict[str, Snapshot],
    target_index: dict[str, object],
    ledger_ids: set[str],
    root: Path = ROOT,
) -> list[str]:
    errors = validate_against_schema(
        data, load_target_evidence_schema(), "evidence"
    )
    if errors:
        return errors

    assert isinstance(data, dict)
    files = {row["path"]: row for row in target_index["files"]}
    seen: set[str] = set()
    for index, row in enumerate(data["records"]):
        prefix = f"evidence.records[{index}]"
        evidence_id = row["evidence_id"]
        if evidence_id in seen:
            errors.append(f"{prefix}.evidence_id: duplicate {evidence_id}")
        seen.add(evidence_id)

        for source_id in row["source_ids"]:
            if source_id not in ledger_ids:
                errors.append(f"{prefix}.source_ids: unknown {source_id}")
        for decision_ref in row["decision_refs"]:
            if decision_ref not in DECISION_REFS:
                errors.append(
                    f"{prefix}.decision_refs: disallowed {decision_ref}"
                )
            elif not (root / decision_ref).is_file():
                errors.append(f"{prefix}.decision_refs: missing {decision_ref}")

        if row["path"] is not None:
            file_row = files.get(row["path"])
            if file_row is None:
                errors.append(f"{prefix}.path: not in target index")
            elif row["start_line"] is None and file_row["kind"] != "binary":
                errors.append(
                    f"{prefix}.path: file-only evidence requires indexed binary"
                )
            elif row["start_line"] is not None and file_row["line_count"] is None:
                errors.append(f"{prefix}.path: binary file cannot have line range")
            elif (
                row["end_line"] is not None
                and row["end_line"] > file_row["line_count"]
            ):
                errors.append(
                    f"{prefix}.end_line: exceeds {row['path']} line_count"
                )
            if (
                row["start_line"] is not None
                and row["start_line"] > row["end_line"]
            ):
                errors.append(f"{prefix}: start_line exceeds end_line")
            target_snapshot = target_index["snapshot"]["snapshot_id"]
            if row["snapshot_id"] != target_snapshot:
                errors.append(
                    f"{prefix}.snapshot_id: expected target snapshot "
                    f"{target_snapshot}"
                )
    return errors


def load_evidence(path: Path) -> dict[str, Evidence]:
    data = json.loads(path.read_text(encoding="utf-8"))
    registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
    target_index = json.loads(
        (
            ROOT / "research/indexes/qwen3-tts-022e286b.json"
        ).read_text(encoding="utf-8")
    )
    with (ROOT / "research/source-ledger.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        ledger_ids = {
            row["source_id"] for row in csv.DictReader(handle)
        }
    errors = validate_evidence(data, registry, target_index, ledger_ids, ROOT)
    if errors:
        raise ValueError("invalid target evidence:\n" + "\n".join(errors))

    return {
        row["evidence_id"]: Evidence(
            evidence_id=row["evidence_id"],
            snapshot_id=row["snapshot_id"],
            path=row["path"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            state=row["state"],
            claim=row["claim"],
            quote=row["quote"],
            source_ids=tuple(row["source_ids"]),
            decision_refs=tuple(row["decision_refs"]),
        )
        for row in data["records"]
    }


def fixed_url(
    row: Evidence, registry: dict[str, Snapshot]
) -> str | None:
    if row.snapshot_id is None or row.path is None:
        return None
    template = registry[row.snapshot_id].blob_url_template
    if row.start_line is None:
        return template.split("#", 1)[0].format(path=row.path)
    return template.format(
        path=row.path, start=row.start_line, end=row.end_line
    )


def validate_target_coverage(
    index: dict[str, object],
    rows: Path | list[dict[str, str]],
    evidence: dict[str, Evidence] | None = None,
    page_catalog: list[dict[str, object]] | None = None,
) -> list[str]:
    if evidence is None:
        evidence = load_evidence(ROOT / "research/target-evidence.json")
    errors: list[str] = []
    if isinstance(rows, Path):
        with rows.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            csv_rows = list(reader)
            if reader.fieldnames != list(COVERAGE_FIELDS):
                errors.append(
                    "target coverage: expected header "
                    + ",".join(COVERAGE_FIELDS)
                )
    elif isinstance(rows, list):
        csv_rows = rows
    else:
        errors.append("target coverage: expected rows array")
        csv_rows = []

    normalized_rows: list[tuple[int, dict[str, str]]] = []
    actual_paths: list[str] = []
    for index_number, row in enumerate(csv_rows):
        if not isinstance(row, Mapping):
            errors.append(f"coverage[{index_number}]: expected object")
            continue
        path_value = row.get("path")
        path = path_value if isinstance(path_value, str) else ""
        prefix = f"coverage[{index_number}]"
        if path:
            prefix += f" {path}"
        normalized: dict[str, str] = {}
        for field in COVERAGE_FIELDS:
            if field not in row:
                normalized[field] = ""
                continue
            value = row.get(field)
            if not isinstance(value, str):
                errors.append(f"{prefix}.{field}: expected string")
                normalized[field] = ""
            else:
                normalized[field] = value
        normalized_rows.append((index_number, normalized))
        if path:
            actual_paths.append(path)

    expected = collections.Counter(row["path"] for row in index["files"])
    actual = collections.Counter(actual_paths)
    for path in sorted((expected - actual).elements()):
        errors.append(f"target coverage: missing {path}")
    for path in sorted((actual - expected).elements()):
        errors.append(f"target coverage: unexpected or duplicate {path}")

    known = set(evidence)
    catalog = None
    if page_catalog is not None:
        catalog = {}
        if not isinstance(page_catalog, list):
            errors.append("page_catalog: expected array")
        else:
            for page_index, page_row in enumerate(page_catalog):
                page_prefix = f"page_catalog[{page_index}]"
                if not isinstance(page_row, Mapping):
                    errors.append(f"{page_prefix}: expected object")
                    continue
                slug = page_row.get("slug")
                if "slug" not in page_row:
                    errors.append(f"{page_prefix}: missing field slug")
                elif not isinstance(slug, str):
                    errors.append(f"{page_prefix}.slug: expected string")
                sections = page_row.get("sections")
                if "sections" not in page_row:
                    errors.append(f"{page_prefix}: missing field sections")
                    continue
                if not isinstance(sections, list):
                    errors.append(f"{page_prefix}.sections: expected array")
                    continue
                valid_ids: set[str] = set()
                for section_index, section_row in enumerate(sections):
                    section_prefix = (
                        f"{page_prefix}.sections[{section_index}]"
                    )
                    if not isinstance(section_row, Mapping):
                        errors.append(f"{section_prefix}: expected object")
                        continue
                    section_id = section_row.get("id")
                    if "id" not in section_row:
                        errors.append(f"{section_prefix}: missing field id")
                    elif not isinstance(section_id, str):
                        errors.append(
                            f"{section_prefix}.id: expected string"
                        )
                    else:
                        valid_ids.add(section_id)
                if isinstance(slug, str):
                    catalog.setdefault(slug, set()).update(valid_ids)

    for index_number, row in normalized_rows:
        prefix = f"coverage[{index_number}]"
        if row["path"]:
            prefix += f" {row['path']}"
        disposition = row["disposition"]
        page = row["page"]
        section = row["section"]
        if disposition not in DISPOSITIONS:
            errors.append(f"{prefix}: invalid disposition {disposition}")
        if disposition in {"mapped", "pending"} and (
            not page or not section
        ):
            errors.append(f"{prefix}: page and section required")
        if disposition in {"excluded", "pending"} and not row["reason"]:
            errors.append(f"{prefix}: reason required")
        for evidence_id in filter(
            None, row["evidence_ids"].split("|")
        ):
            if evidence_id not in known:
                errors.append(f"{prefix}: unknown evidence {evidence_id}")
        if (
            catalog is not None
            and disposition in {"mapped", "pending"}
            and page
            and section
        ):
            if (
                page not in catalog
                or section not in catalog[page]
            ):
                errors.append(
                    f"{prefix}: missing section {page}#{section}"
                )
    return errors


@dataclass(frozen=True)
class HtmlLink:
    url: str
    fragment: str


@dataclass(frozen=True)
class HtmlAnchor:
    attributes: dict[str, str]


class ParsedHtml:
    def __init__(self) -> None:
        self.ids: set[str] = set()
        self.headings: list[int] = []
        self.local_links: list[HtmlLink] = []
        self.anchors: list[HtmlAnchor] = []
        self.aria_controls: list[str] = []
        self.remote_resources: list[str] = []
        self.remote_anchors: list[str] = []
        self.evidence_states: list[str] = []


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.document = ParsedHtml()

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {key: (value or "") for key, value in attrs}
        if attributes.get("id"):
            self.document.ids.add(attributes["id"])
        if re.fullmatch(r"h[1-6]", tag):
            self.document.headings.append(int(tag[1]))
        if attributes.get("aria-controls"):
            self.document.aria_controls.extend(
                attributes["aria-controls"].split()
            )
        if "data-evidence-state" in attributes:
            self.document.evidence_states.append(
                attributes["data-evidence-state"]
            )

        if tag == "a":
            self.document.anchors.append(HtmlAnchor(attributes))
            self._collect_link(attributes.get("href", ""), runtime=False)
        elif tag == "form":
            self._collect_link(attributes.get("action", ""), runtime=True)
        elif tag in {"script", "img", "audio", "video", "source"}:
            self._collect_link(attributes.get("src", ""), runtime=True)
        elif tag == "link" and attributes.get("href"):
            rel = set(attributes.get("rel", "").casefold().split())
            if rel & {"stylesheet", "preload", "modulepreload", "icon"}:
                self._collect_link(attributes["href"], runtime=True)

        for key in ("data-search-url", "data-search-index", "data-search-data"):
            if attributes.get(key):
                self._collect_link(attributes[key], runtime=True)

    def _collect_link(self, url: str, *, runtime: bool) -> None:
        if not url:
            return
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme or parsed.netloc:
            if runtime:
                self.document.remote_resources.append(url)
            elif parsed.scheme != "https":
                self.document.remote_anchors.append(url)
            return
        self.document.local_links.append(
            HtmlLink(url=url, fragment=urllib.parse.unquote(parsed.fragment))
        )


def parse_html(path: Path) -> ParsedHtml:
    parser = _DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.document


def expected_generated_outputs(pages) -> set[str]:
    return {page["slug"] for page in pages} | {"assets/search-index.json"}


def actual_generated_outputs(site_root: Path) -> set[str]:
    html = {
        path.relative_to(site_root).as_posix()
        for path in site_root.rglob("*.html")
    }
    search = site_root / "assets/search-index.json"
    return html | ({"assets/search-index.json"} if search.is_file() else set())


def _block_evidence_ids(block):
    yield from block.get("evidence_ids", [])
    for item in block.get("items", []):
        yield from item.get("evidence_ids", [])


def validate_cross_contracts(pages, evidence, coverage) -> list[str]:
    errors: list[str] = []
    known_evidence = set(evidence)
    catalog = {
        page["slug"]: {
            section["id"]: section for section in page["sections"]
        }
        for page in pages
    }
    section_evidence: dict[tuple[str, str], set[str]] = {}
    page_evidence: set[str] = set()

    for page in pages:
        for section in page["sections"]:
            refs = {
                evidence_id
                for block in section["blocks"]
                for evidence_id in _block_evidence_ids(block)
            }
            section_evidence[(page["slug"], section["id"])] = refs
            page_evidence.update(refs)
            for evidence_id in sorted(refs - known_evidence):
                errors.append(
                    f"page {page['slug']}#{section['id']}: unknown evidence "
                    f"{evidence_id}"
                )

    from scripts.site_builder import load_all_indexes

    target = load_all_indexes()["qwen3-tts-022e286b"]
    target_paths = collections.Counter(row["path"] for row in target["files"])
    coverage_paths = collections.Counter(row["path"] for row in coverage)
    for path in sorted((target_paths - coverage_paths).elements()):
        errors.append(f"target coverage: missing {path}")
    for path in sorted((coverage_paths - target_paths).elements()):
        errors.append(f"target coverage: unexpected {path}")

    for row in coverage:
        if row["disposition"] not in {"mapped", "pending"}:
            continue
        destination = (row["page"], row["section"])
        if (
            row["page"] not in catalog
            or row["section"] not in catalog[row["page"]]
        ):
            errors.append(
                f"coverage {row['path']}: missing section "
                f"{row['page']}#{row['section']}"
            )
            continue
        for evidence_id in filter(None, row["evidence_ids"].split("|")):
            if evidence_id not in known_evidence:
                errors.append(
                    f"coverage {row['path']}: unknown evidence {evidence_id}"
                )
            elif evidence_id not in section_evidence[destination]:
                errors.append(
                    f"coverage {row['path']}: evidence {evidence_id} absent from "
                    f"{row['page']}#{row['section']}"
                )

    important = {
        "TGT-SCOPE-002",
        "TGT-TOK25-002",
        "PH1-ROLE-MM",
        "PH1-ROLE-LLM",
        "PH1-ROLE-MOSS",
        "PH1-ENV-LANES",
    }
    for evidence_id in sorted(important - page_evidence):
        errors.append(
            f"important evidence {evidence_id}: not referenced by any page"
        )
    return errors


def _resolve_local_target(site_root: Path, page_path: Path, href: str):
    parsed = urllib.parse.urlsplit(href)
    raw_path = urllib.parse.unquote(parsed.path)
    candidate = (
        page_path.resolve()
        if not raw_path
        else (page_path.parent / raw_path).resolve()
    )
    resolved_site = site_root.resolve()
    allowed = {(site_root.parent / ref).resolve() for ref in DECISION_REFS}
    relative = page_path.relative_to(site_root).as_posix()
    if not candidate.is_relative_to(resolved_site):
        if candidate not in allowed:
            return None, f"{relative}: local link escapes site {href}"
        if not candidate.is_file():
            return None, f"{relative}: broken local link {href}"
    elif not candidate.is_file():
        return None, f"{relative}: broken local link {href}"
    return candidate, None


def validate_document_structure(
    relative: str, parsed: ParsedHtml, evidence
) -> list[str]:
    errors: list[str] = []
    h1_count = parsed.headings.count(1)
    if h1_count != 1:
        errors.append(f"{relative}: expected one h1, found {h1_count}")
    previous = 0
    for level in parsed.headings:
        if previous and level > previous + 1:
            errors.append(
                f"{relative}: heading level jumps h{previous} to h{level}"
            )
        previous = level
    for state in parsed.evidence_states:
        if state not in EVIDENCE_STATES:
            errors.append(f"{relative}: invalid evidence status {state}")
    return errors


def validate_aria_references(
    source_path: Path, parsed: ParsedHtml, site_root: Path | None = None
) -> list[str]:
    root = site_root or source_path.parent
    relative = source_path.relative_to(root).as_posix()
    return [
        f"{relative}: aria-controls {control} has no matching id"
        for control in parsed.aria_controls
        if control not in parsed.ids
    ]


def validate_remote_resources(
    source_path: Path, parsed: ParsedHtml, site_root: Path | None = None
) -> list[str]:
    root = site_root or source_path.parent
    relative = source_path.relative_to(root).as_posix()
    errors = [
        f"{relative}: remote runtime resource {url}"
        for url in parsed.remote_resources
    ]
    errors.extend(
        f"{relative}: external anchor must use https {url}"
        for url in parsed.remote_anchors
    )
    return errors


def validate_generated_site(
    site_root,
    pages,
    evidence,
    coverage,
    catalog_paths=PHASE2_CATALOG_PATHS,
) -> list[str]:
    # Normalize once so macOS' /var -> /private/var alias cannot make
    # otherwise identical paths fail relative_to checks.
    site_root = Path(site_root).resolve()
    errors = validate_cross_contracts(pages, evidence, coverage)
    expected = expected_generated_outputs(pages)
    actual = actual_generated_outputs(site_root)
    for relative in sorted(expected - actual):
        errors.append(f"site: missing generated output {relative}")
    for relative in sorted(actual - expected):
        errors.append(f"site: unexpected generated output {relative}")

    parsed_pages: dict[Path, ParsedHtml] = {}
    for relative in sorted(expected & actual):
        if not relative.endswith(".html"):
            continue
        path = site_root / relative
        parsed = parse_html(path)
        parsed_pages[path.resolve()] = parsed
        errors.extend(validate_document_structure(relative, parsed, evidence))

    for source_path, parsed in parsed_pages.items():
        for link in parsed.local_links:
            target, error = _resolve_local_target(
                site_root, source_path, link.url
            )
            if error:
                errors.append(error)
                continue
            if link.fragment and target.suffix == ".html":
                target_doc = parsed_pages.get(target) or parse_html(target)
                if link.fragment not in target_doc.ids:
                    errors.append(
                        f"{source_path.relative_to(site_root).as_posix()}: "
                        f"broken fragment {link.url}"
                    )
        errors.extend(
            validate_aria_references(source_path, parsed, site_root)
        )
        errors.extend(
            validate_remote_resources(source_path, parsed, site_root)
        )

    with tempfile.TemporaryDirectory() as tmp:
        from scripts.site_builder import build_site

        fresh_root = Path(tmp) / "site"
        build_site(fresh_root, list(catalog_paths))
        for relative in sorted(expected):
            current = site_root / relative
            fresh = fresh_root / relative
            if (
                current.is_file()
                and fresh.is_file()
                and current.read_bytes() != fresh.read_bytes()
            ):
                errors.append(f"site: generated output differs {relative}")
    return errors


def _expected_fixed_url(
    snapshot, source_path, start=None, end=None, file_only=False
):
    if file_only:
        return snapshot.blob_url_template.split("#L", 1)[0].format(
            path=source_path
        )
    return snapshot.blob_url_template.format(
        path=source_path, start=start, end=end
    )


def validate_fixed_links(site_root: Path, registry) -> list[str]:
    from scripts.site_builder import load_all_indexes

    errors: list[str] = []
    indexes = load_all_indexes()
    html_paths = sorted(site_root.rglob("*.html"))
    if len(html_paths) != 13:
        errors.append(
            f"fixed links: expected 13 HTML pages, found {len(html_paths)}"
        )
    repository_blob_prefixes = tuple(
        snapshot.blob_url_template.partition("/blob/")[0] + "/blob/"
        for snapshot in registry.values()
    )

    for page_path in html_paths:
        relative = page_path.relative_to(site_root).as_posix()
        document = parse_html(page_path)
        for anchor in document.anchors:
            attrs = anchor.attributes
            href = attrs.get("href", "")
            marked = "data-fixed-source-link" in attrs
            if href.startswith(repository_blob_prefixes) and not marked:
                errors.append(f"{relative}: unmarked fixed source link {href}")
                continue
            if not marked:
                continue
            snapshot_id = attrs.get("data-snapshot-id", "")
            source_path = attrs.get("data-source-path", "")
            if snapshot_id not in registry:
                errors.append(
                    f"{relative}: fixed link unknown snapshot {snapshot_id}"
                )
                continue
            snapshot = registry[snapshot_id]
            revision = href.partition("/blob/")[2].partition("/")[0]
            if revision in {"main", "master"}:
                errors.append(
                    f"{relative}: fixed link {snapshot_id}: moving revision "
                    f"{revision}"
                )
                continue
            if revision != snapshot.revision:
                errors.append(
                    f"{relative}: fixed link {snapshot_id}: revision "
                    f"{revision} expected {snapshot.revision}"
                )
                continue
            indexed = {
                row["path"]: row for row in indexes[snapshot_id]["files"]
            }
            if source_path not in indexed:
                errors.append(
                    f"{relative}: fixed link {snapshot_id}: unknown path "
                    f"{source_path}"
                )
                continue
            row = indexed[source_path]
            file_only = attrs.get("data-file-only") == "true"
            if row["kind"] == "binary":
                if (
                    not file_only
                    or "#" in href
                    or "data-start-line" in attrs
                    or "data-end-line" in attrs
                ):
                    errors.append(
                        f"{relative}: binary fixed link {snapshot_id}:"
                        f"{source_path} must be file-only"
                    )
                    continue
                expected_url = _expected_fixed_url(
                    snapshot, source_path, file_only=True
                )
            else:
                try:
                    start = int(attrs["data-start-line"])
                    end = int(attrs["data-end-line"])
                except (KeyError, ValueError):
                    errors.append(
                        f"{relative}: text fixed link {snapshot_id}:"
                        f"{source_path} missing line range"
                    )
                    continue
                if file_only or not (1 <= start <= end <= row["line_count"]):
                    errors.append(
                        f"{relative}: text fixed link {snapshot_id}:"
                        f"{source_path} invalid line range {start}-{end}"
                    )
                    continue
                expected_url = _expected_fixed_url(
                    snapshot, source_path, start, end
                )
            if href != expected_url:
                errors.append(
                    f"{relative}: fixed link {snapshot_id}:{source_path} "
                    "URL mismatch"
                )
    return errors


RESTRICTED_DIRS = {
    "model",
    "models",
    "weight",
    "weights",
    "dataset",
    "datasets",
    "data",
    "checkpoint",
    "checkpoints",
}
RESTRICTED_SUFFIXES = {
    ".pem",
    ".key",
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".bin",
    ".onnx",
    ".h5",
    ".hdf5",
    ".npy",
    ".npz",
    ".parquet",
    ".arrow",
    ".feather",
    ".tfrecord",
    ".mdb",
    ".sqlite",
    ".db",
    ".jsonl",
    ".gguf",
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
}
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"


def validate_public_tracking(root: Path, tracked_paths=None) -> list[str]:
    if tracked_paths is None:
        raw = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        tracked_paths = [
            os.fsdecode(item) for item in raw.split(b"\0") if item
        ]
    errors: list[str] = []
    for value in tracked_paths:
        relative = os.fsdecode(value)
        parts = PurePosixPath(relative).parts
        lowered = tuple(part.casefold() for part in parts)
        private_checkout = any(
            lowered[index] == ".superpowers"
            and index + 1 < len(lowered)
            and lowered[index + 1] == "source-checkouts"
            for index in range(len(lowered))
        )
        references_dir = "references" in lowered[:-1]
        env_file = any(
            part == ".env" or part.startswith(".env.") for part in lowered
        )
        restricted_dir = any(
            part in RESTRICTED_DIRS for part in lowered[:-1]
        )
        restricted_suffix = (
            PurePosixPath(relative).suffix.casefold() in RESTRICTED_SUFFIXES
        )
        if (
            private_checkout
            or references_dir
            or env_file
            or restricted_dir
            or restricted_suffix
        ):
            errors.append(f"public tracking: restricted path {relative}")
            continue
        candidate = root / relative
        if candidate.is_file():
            with candidate.open("rb") as handle:
                if handle.read(len(LFS_HEADER)) == LFS_HEADER:
                    errors.append(
                        f"public tracking: Git LFS pointer {relative}"
                    )
    return errors
