"""Strict contracts for Phase 3 reference-project evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.phase2_contracts import EVIDENCE_STATES, Snapshot


@dataclass(frozen=True)
class ReferenceEvidence:
    evidence_id: str
    snapshot_id: str | None
    path: str | None
    start_line: int | None
    end_line: int | None
    state: str
    claim: str
    source_ids: tuple[str, ...]
    verification_condition: str


REFERENCE_COVERAGE_FIELDS = (
    "surface", "disposition", "page", "section", "evidence_ids", "reason"
)
REFERENCE_DISPOSITIONS = {"mapped", "excluded", "pending"}
PHASE3_CATALOG_PATHS = (
    Path("content/reference-mindspeed-mm.json"),
    Path("content/reference-mindspeed-llm.json"),
    Path("content/reference-moss-tts.json"),
    Path("content/migration-mapping.json"),
)


def _relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _file_lines(index: dict[str, object], path: str) -> int | None:
    files = index.get("files", [])
    if not isinstance(files, list):
        return None
    for row in files:
        if isinstance(row, dict) and row.get("path") == path:
            lines = row.get("line_count")
            return lines if isinstance(lines, int) else None
    return None


def _errors_for_record(record, registry, indexes, seen):
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["evidence: expected object"]
    allowed = {
        "evidence_id", "snapshot_id", "path", "start_line", "end_line",
        "state", "claim", "source_ids", "verification_condition",
    }
    unknown = set(record) - allowed
    if unknown:
        errors.append(f"evidence: unknown field {sorted(unknown)[0]}")
    evidence_id = record.get("evidence_id")
    if not isinstance(evidence_id, str) or not evidence_id:
        errors.append("evidence_id: expected non-empty string")
    elif evidence_id in seen:
        errors.append(f"evidence_id: duplicate {evidence_id}")
    else:
        seen.add(evidence_id)
    state = record.get("state")
    if state not in EVIDENCE_STATES:
        errors.append(f"state: unknown {state}")
    if not isinstance(record.get("claim"), str) or not record.get("claim"):
        errors.append("claim: expected non-empty string")
    source_ids = record.get("source_ids")
    if not isinstance(source_ids, list) or not all(isinstance(item, str) for item in source_ids):
        errors.append("source_ids: expected string array")
    snapshot_id = record.get("snapshot_id")
    path = record.get("path")
    start, end = record.get("start_line"), record.get("end_line")
    if snapshot_id is None:
        if any(value is not None for value in (path, start, end)):
            errors.append("source location: null snapshot requires null path and lines")
    elif snapshot_id not in registry:
        errors.append(f"snapshot_id: unknown {snapshot_id}")
    elif not _relative_path(path):
        errors.append("path: expected relative POSIX materialized path")
    else:
        lines = _file_lines(indexes.get(snapshot_id, {}), path)
        if lines is None:
            errors.append(f"path: not materialized {path}")
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
            errors.append("line range: expected positive ordered integers")
        elif lines is not None and end > lines:
            errors.append(f"line range: end {end} exceeds {lines}")
    condition = record.get("verification_condition")
    if not isinstance(condition, str):
        errors.append("verification_condition: expected string")
    elif state == "pending_hardware" and not condition.strip():
        errors.append("verification_condition: required for pending_hardware")
    return errors


def load_reference_evidence(path: Path, registry: dict[str, Snapshot], indexes: dict[str, dict[str, object]]) -> dict[str, ReferenceEvidence]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "evidence"} or data.get("schema_version") != 1 or not isinstance(data.get("evidence"), list):
        raise ValueError("reference evidence: expected schema_version 1 and evidence array")
    seen: set[str] = set()
    errors: list[str] = []
    for record in data["evidence"]:
        errors.extend(_errors_for_record(record, registry, indexes, seen))
    if errors:
        raise ValueError("\n".join(errors))
    return {
        record["evidence_id"]: ReferenceEvidence(
            record["evidence_id"], record["snapshot_id"], record["path"],
            record["start_line"], record["end_line"], record["state"],
            record["claim"], tuple(record["source_ids"]),
            record["verification_condition"],
        )
        for record in data["evidence"]
    }


def validate_reference_coverage(rows, surfaces: set[str], evidence: dict[str, ReferenceEvidence]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("coverage: expected object")
            continue
        if set(row) != set(REFERENCE_COVERAGE_FIELDS):
            errors.append("coverage: unexpected fields")
            continue
        surface = row["surface"]
        if surface in seen:
            errors.append(f"coverage: duplicate surface {surface}")
        seen.add(surface)
        if surface not in surfaces:
            errors.append(f"coverage: unknown surface {surface}")
        if row["disposition"] not in REFERENCE_DISPOSITIONS:
            errors.append(f"coverage: unknown disposition {row['disposition']}")
        for evidence_id in filter(None, row["evidence_ids"].split(";")):
            if evidence_id not in evidence:
                errors.append(f"coverage: unknown evidence {evidence_id}")
    for surface in sorted(surfaces - seen):
        errors.append(f"coverage: missing surface {surface}")
    return errors
