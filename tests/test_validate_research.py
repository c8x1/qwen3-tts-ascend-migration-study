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


def read_csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


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
        rows = read_csv(path)
        rows[1][10] = "81"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("CAND-001: total 81 does not equal 80", validate_research(self.root))

    def test_source_grade_must_be_known(self) -> None:
        path = self.root / "research" / "source-ledger.csv"
        rows = read_csv(path)
        rows[1][4] = "Z"
        write_csv(path, rows[0], rows[1:])
        self.assertIn("SRC-001: invalid source_grade Z", validate_research(self.root))

    def test_methodology_defines_phase_hard_gates(self) -> None:
        methodology = Path(__file__).parents[1] / "research" / "methodology.md"
        content = methodology.read_text(encoding="utf-8")
        required_contracts = [
            "## Scope and hard gates",
            "Ascend 910B",
            "CANN 8.5.2",
            "PyTorch 2.7.1",
            "预训练、SFT、推理验证、单机 8 卡和多机多卡",
            "MindSpeed/MindSpeed-LLM",
            "成熟参考项目",
            "主参考项目",
            "专项卫星",
        ]
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, content)

    def test_audited_candidate_requires_evidence(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        rows[1][12] = ""
        write_csv(path, rows[0], rows[1:])

        self.assertIn(
            "CAND-001: audited candidate requires evidence_ids",
            validate_research(self.root),
        )

    def test_recommended_candidate_requires_evidence(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        rows[1][11] = "recommended"
        rows[1][12] = ""
        write_csv(path, rows[0], rows[1:])

        self.assertIn(
            "CAND-001: recommended candidate requires evidence_ids",
            validate_research(self.root),
        )

    def test_rejected_candidate_requires_evidence_or_exclusion_reason(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        rows[1][11] = "rejected"
        rows[1][12] = ""
        rows[1][13] = ""
        write_csv(path, rows[0], rows[1:])

        self.assertIn(
            "CAND-001: rejected candidate requires evidence_ids or exclusion_reason",
            validate_research(self.root),
        )

    def test_rejected_candidate_may_use_exclusion_reason_without_evidence(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        rows[1][11] = "rejected"
        rows[1][12] = ""
        rows[1][13] = "duplicate mirror"
        write_csv(path, rows[0], rows[1:])

        self.assertEqual(validate_research(self.root), [])

    def test_query_id_must_be_nonempty(self) -> None:
        path = self.root / "research" / "search-log.csv"
        write_csv(
            path,
            SEARCH_HEADER,
            [["", "GitHub", "qwen ascend", "2026-07-17T10:00:00+08:00", "5", "", ""]],
        )

        self.assertIn("duplicate or empty query_id: ", validate_research(self.root))

    def test_query_id_must_be_unique(self) -> None:
        path = self.root / "research" / "search-log.csv"
        query = ["QRY-001", "GitHub", "qwen ascend", "2026-07-17T10:00:00+08:00", "5", "", ""]
        write_csv(path, SEARCH_HEADER, [query, query])

        self.assertIn("duplicate or empty query_id: QRY-001", validate_research(self.root))

    def test_search_run_at_requires_timezone_aware_iso_8601(self) -> None:
        path = self.root / "research" / "search-log.csv"
        write_csv(
            path,
            SEARCH_HEADER,
            [["QRY-001", "GitHub", "qwen ascend", "2026-07-17T10:00:00", "5", "", ""]],
        )

        self.assertIn(
            "QRY-001: invalid or timezone-naive run_at 2026-07-17T10:00:00",
            validate_research(self.root),
        )

    def test_search_result_count_must_be_nonnegative_integer(self) -> None:
        path = self.root / "research" / "search-log.csv"
        for result_count in ["many", "-1"]:
            with self.subTest(result_count=result_count):
                write_csv(
                    path,
                    SEARCH_HEADER,
                    [["QRY-001", "GitHub", "qwen ascend", "2026-07-17T10:00:00+08:00", result_count, "", ""]],
                )
                self.assertIn(
                    f"QRY-001: invalid result_count {result_count}",
                    validate_research(self.root),
                )

    def test_search_accepted_ids_must_reference_candidates(self) -> None:
        path = self.root / "research" / "search-log.csv"
        write_csv(
            path,
            SEARCH_HEADER,
            [["QRY-001", "GitHub", "qwen ascend", "2026-07-17T10:00:00+08:00", "5", "CAND-404", ""]],
        )

        self.assertIn("QRY-001: unknown accepted_id CAND-404", validate_research(self.root))

    def test_missing_candidate_column_returns_error_instead_of_raising(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        write_csv(path, rows[0], [rows[1][:-1]])

        try:
            errors = validate_research(self.root)
        except Exception as error:  # pragma: no cover - turns the regression into a clear failure
            self.fail(f"validate_research raised {type(error).__name__}: {error}")
        self.assertTrue(
            any(error.endswith(": row 2 has missing or extra fields") for error in errors),
            errors,
        )

    def test_extra_candidate_column_returns_error_instead_of_raising(self) -> None:
        path = self.root / "research" / "candidates.csv"
        rows = read_csv(path)
        write_csv(path, rows[0], [rows[1] + ["unexpected"]])

        errors = validate_research(self.root)
        self.assertTrue(
            any(error.endswith(": row 2 has missing or extra fields") for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
