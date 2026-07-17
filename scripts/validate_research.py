from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


SOURCE_HEADER = [
    "source_id", "title", "url", "publisher", "source_grade",
    "accessed_at", "used_for", "archive_status",
]
SEARCH_HEADER = [
    "query_id", "channel", "query", "run_at", "result_count",
    "accepted_ids", "notes",
]
CANDIDATE_HEADER = [
    "candidate_id", "name", "url", "revision", "license",
    "ascend_completeness", "architecture_proximity", "scale_maturity",
    "reproducibility", "docs_license", "total", "status",
    "evidence_ids", "exclusion_reason",
]
SCORE_LIMITS = {
    "ascend_completeness": 30,
    "architecture_proximity": 25,
    "scale_maturity": 20,
    "reproducibility": 15,
    "docs_license": 10,
}
SOURCE_GRADES = {"S", "A", "B", "C"}
ARCHIVE_STATES = {"live", "mirror", "unavailable"}
CANDIDATE_STATES = {"discovered", "shortlisted", "audited", "rejected", "recommended"}


def read_rows(path: Path, expected_header: list[str], errors: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_header:
            errors.append(f"{path}: invalid header")
            return []
        return list(reader)


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_research(root: Path) -> list[str]:
    errors: list[str] = []
    research = root / "research"
    sources = read_rows(research / "source-ledger.csv", SOURCE_HEADER, errors)
    read_rows(research / "search-log.csv", SEARCH_HEADER, errors)
    candidates = read_rows(research / "candidates.csv", CANDIDATE_HEADER, errors)

    source_ids: set[str] = set()
    for row in sources:
        source_id = row["source_id"]
        if not source_id or source_id in source_ids:
            errors.append(f"duplicate or empty source_id: {source_id}")
        source_ids.add(source_id)
        if row["source_grade"] not in SOURCE_GRADES:
            errors.append(f"{source_id}: invalid source_grade {row['source_grade']}")
        if row["archive_status"] not in ARCHIVE_STATES:
            errors.append(f"{source_id}: invalid archive_status {row['archive_status']}")
        if not valid_url(row["url"]):
            errors.append(f"{source_id}: invalid URL {row['url']}")
        try:
            date.fromisoformat(row["accessed_at"])
        except ValueError:
            errors.append(f"{source_id}: invalid accessed_at {row['accessed_at']}")

    candidate_ids: set[str] = set()
    for row in candidates:
        candidate_id = row["candidate_id"]
        if not candidate_id or candidate_id in candidate_ids:
            errors.append(f"duplicate or empty candidate_id: {candidate_id}")
        candidate_ids.add(candidate_id)
        if row["status"] not in CANDIDATE_STATES:
            errors.append(f"{candidate_id}: invalid status {row['status']}")
        if not valid_url(row["url"]):
            errors.append(f"{candidate_id}: invalid URL {row['url']}")

        scores: dict[str, int] = {}
        for field, maximum in SCORE_LIMITS.items():
            try:
                value = int(row[field])
            except ValueError:
                errors.append(f"{candidate_id}: {field} is not an integer")
                value = 0
            if not 0 <= value <= maximum:
                errors.append(f"{candidate_id}: {field} {value} outside 0..{maximum}")
            scores[field] = value
        expected_total = sum(scores.values())
        try:
            total = int(row["total"])
        except ValueError:
            errors.append(f"{candidate_id}: total is not an integer")
            total = -1
        if total != expected_total:
            errors.append(f"{candidate_id}: total {total} does not equal {expected_total}")

        for source_id in filter(None, row["evidence_ids"].split("|")):
            if source_id not in source_ids:
                errors.append(f"{candidate_id}: unknown evidence_id {source_id}")

    return errors


def main() -> int:
    errors = validate_research(Path.cwd())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("research data valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
