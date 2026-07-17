import csv
import tempfile
import unittest
from pathlib import Path

from scripts.validate_research import validate_research


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


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


class ValidateResearchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        research = self.root / "research"
        research.mkdir()
        write_csv(
            research / "source-ledger.csv",
            SOURCE_HEADER,
            [["SRC-001", "Official source", "https://example.com/doc", "Vendor", "S", "2026-07-16", "training support", "live"]],
        )
        write_csv(research / "search-log.csv", SEARCH_HEADER, [])
        write_csv(
            research / "candidates.csv",
            CANDIDATE_HEADER,
            [["CAND-001", "Example", "https://example.com/repo", "abc123", "Apache-2.0", "25", "20", "15", "12", "8", "80", "audited", "SRC-001", ""]],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_research_data_has_no_errors(self) -> None:
        self.assertEqual(validate_research(self.root), [])

    def test_score_total_must_equal_dimensions(self) -> None:
        path = self.root / "research" / "candidates.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        rows[1][10] = "81"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("CAND-001: total 81 does not equal 80", validate_research(self.root))

    def test_source_grade_must_be_known(self) -> None:
        path = self.root / "research" / "source-ledger.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        rows[1][4] = "Z"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("SRC-001: invalid source_grade Z", validate_research(self.root))


if __name__ == "__main__":
    unittest.main()
