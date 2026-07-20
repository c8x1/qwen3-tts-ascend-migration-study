"""Contracts for immutable source snapshots and generated source indexes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parents[1]
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
                errors.append(f"{row_path}.{field}: expected nonempty string")

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
                for path_index, excluded_path in enumerate(paths):
                    item_path = f"{row_path}.excluded.paths[{path_index}]"
                    if not _relative_posix(excluded_path):
                        errors.append(f"{item_path}: expected relative POSIX path")
                    elif excluded_path in seen_paths:
                        errors.append(f"{item_path}: duplicate path {excluded_path}")
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


def _validate_schema(value: object, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    variants = schema.get("oneOf")
    if isinstance(variants, list):
        matches = 0
        for variant in variants:
            variant_errors: list[str] = []
            if isinstance(variant, dict):
                _validate_schema(value, variant, path, variant_errors)
            else:
                variant_errors.append(f"{path}: invalid schema variant")
            if not variant_errors:
                matches += 1
        if matches != 1:
            errors.append(f"{path}: expected exactly one allowed shape")
        return

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _json_type_matches(value, expected_type):
        errors.append(f"{path}: expected {expected_type}")
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
                if field not in _FORBIDDEN_KEYS:
                    errors.append(f"{path}: unknown field {field}")
        for field in sorted(set(value) & set(properties)):
            child_schema = properties[field]
            if isinstance(child_schema, dict):
                child_path = f"{path}.{field}"
                _validate_schema(value[field], child_schema, child_path, errors)

    if isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema(item, item_schema, f"{path}[{index}]", errors)

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']}")
    choices = schema.get("enum")
    if isinstance(choices, list) and value not in choices:
        errors.append(f"{path}: expected one of {choices}")
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str) and re.search(pattern, value) is None:
        errors.append(f"{path}: does not match pattern {pattern}")
    minimum = schema.get("minimum")
    if (
        isinstance(minimum, (int, float))
        and not isinstance(minimum, bool)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value < minimum
    ):
        errors.append(f"{path}: expected minimum {minimum}")


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
                f"index.symbols[{index}].path: binary owner has no line count"
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
                f"index.configs[{index}].path: binary owner has no line count"
            )
        elif row["line"] > owner["line_count"]:
            errors.append(
                f"index.configs[{index}].line: exceeds file line_count"
            )

    if data["content_digest"] != _materialized_digest(data):
        errors.append("index.content_digest: does not match materialized content")
    return errors
