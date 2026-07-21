import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.phase2_contracts import load_snapshot_registry
from scripts.phase3_contracts import (
    ReferenceEvidence,
    load_reference_evidence,
    validate_reference_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
MM = "mindspeed-mm-0edd553e"


class ReferenceEvidenceContractTest(unittest.TestCase):
    def setUp(self):
        self.registry = load_snapshot_registry(
            ROOT / "research/source-snapshots.json"
        )
        self.indexes = {
            snapshot_id: json.loads(
                (ROOT / "research/indexes" / f"{snapshot_id}.json").read_text()
            )
            for snapshot_id in self.registry
        }

    def write_payload(self, records):
        temp = TemporaryDirectory()
        path = Path(temp.name) / "evidence.json"
        path.write_text(json.dumps({"schema_version": 1, "evidence": records}))
        self.addCleanup(temp.cleanup)
        return path

    def test_loads_fixed_materialized_source_record(self):
        path = self.write_payload([
            {
                "evidence_id": "REF-MM-001",
                "snapshot_id": MM,
                "path": "README.md",
                "start_line": 1,
                "end_line": 2,
                "state": "verified",
                "claim": "README is a materialized fixed-source file",
                "source_ids": ["SRC-019"],
                "verification_condition": "",
            }
        ])
        evidence = load_reference_evidence(path, self.registry, self.indexes)
        self.assertEqual(evidence["REF-MM-001"].snapshot_id, MM)
        self.assertIsInstance(evidence["REF-MM-001"], ReferenceEvidence)

    def test_public_evidence_loader_uses_approved_phase2_inputs(self):
        path = self.write_payload([{
            "evidence_id": "REF-MM-PUBLIC-001", "snapshot_id": MM,
            "path": "README.md", "start_line": 1, "end_line": 1,
            "state": "verified", "claim": "x", "source_ids": ["SRC-019"],
            "verification_condition": "",
        }])
        evidence = load_reference_evidence(path)
        self.assertIn("REF-MM-PUBLIC-001", evidence)

    def test_source_ids_require_unique_approved_ledger_entries(self):
        for source_ids in ([], ["SRC-019", "SRC-019"], ["SRC-999"], ["not-an-id"]):
            with self.subTest(source_ids=source_ids):
                path = self.write_payload([{
                    "evidence_id": "REF-SOURCE-001", "snapshot_id": MM,
                    "path": "README.md", "start_line": 1, "end_line": 1,
                    "state": "verified", "claim": "x", "source_ids": source_ids,
                    "verification_condition": "",
                }])
                with self.assertRaisesRegex(ValueError, "source_ids"):
                    load_reference_evidence(path, self.registry, self.indexes)

    def test_rejects_duplicate_unknown_and_bad_source_location(self):
        path = self.write_payload([
            {
                "evidence_id": "REF-DUP-001", "snapshot_id": "unknown",
                "path": "/Users/example/private.py", "start_line": 0,
                "end_line": 999999, "state": "bad-state", "claim": "x",
                "source_ids": [], "verification_condition": "",
            },
            {
                "evidence_id": "REF-DUP-001", "snapshot_id": MM,
                "path": "../escape", "start_line": 1, "end_line": 1,
                "state": "verified", "claim": "x", "source_ids": [],
                "verification_condition": "",
            },
        ])
        with self.assertRaisesRegex(ValueError, "duplicate|unknown|absolute|relative|state"):
            load_reference_evidence(path, self.registry, self.indexes)

    def test_pending_hardware_requires_a_verification_condition(self):
        path = self.write_payload([
            {
                "evidence_id": "REF-HW-001", "snapshot_id": MM,
                "path": "README.md", "start_line": 1, "end_line": 1,
                "state": "pending_hardware", "claim": "x", "source_ids": [],
                "verification_condition": "",
            }
        ])
        with self.assertRaisesRegex(ValueError, "verification_condition"):
            load_reference_evidence(path, self.registry, self.indexes)

    def test_null_snapshot_and_binary_or_boolean_lines_fail_closed(self):
        null_path = self.write_payload([{
            "evidence_id": "REF-NULL-001", "snapshot_id": None,
            "path": "README.md", "start_line": 1, "end_line": 1,
            "state": "verified", "claim": "x", "source_ids": [],
            "verification_condition": "",
        }])
        with self.assertRaisesRegex(ValueError, "null snapshot"):
            load_reference_evidence(null_path, self.registry, self.indexes)
        indexes = {key: dict(value) for key, value in self.indexes.items()}
        indexes[MM]["files"] = [{"path": "README.md", "line_count": True, "kind": "text"}]
        bool_path = self.write_payload([{
            "evidence_id": "REF-BOOL-001", "snapshot_id": MM,
            "path": "README.md", "start_line": True, "end_line": True,
            "state": "verified", "claim": "x", "source_ids": [],
            "verification_condition": "",
        }])
        with self.assertRaisesRegex(ValueError, "line"):
            load_reference_evidence(bool_path, self.registry, indexes)

    def test_coverage_requires_one_row_per_surface_and_known_evidence(self):
        evidence = {
            "REF-MM-001": ReferenceEvidence(
                "REF-MM-001", MM, "README.md", 1, 1, "verified", "x", (), ""
            )
        }
        rows = [
            {"surface": "launch", "disposition": "mapped", "page": "reference/mm.html", "section": "entry", "evidence_ids": "REF-MM-001", "reason": ""},
            {"surface": "launch", "disposition": "mapped", "page": "reference/mm.html", "section": "entry", "evidence_ids": "unknown", "reason": ""},
        ]
        errors = validate_reference_coverage(
            rows, {"launch": {}, "checkpoint": {}}, evidence
        )
        self.assertTrue(any("duplicate surface launch" in error for error in errors))
        self.assertTrue(any("missing surface checkpoint" in error for error in errors))
        self.assertTrue(any("unknown evidence unknown" in error for error in errors))

    def test_malformed_coverage_rows_return_errors(self):
        errors = validate_reference_coverage(
            [{"surface": "launch", "evidence_ids": None}],
            {"launch": {}}, {},
        )
        self.assertTrue(errors)
        self.assertTrue(any("expected fields" in error for error in errors))

    def test_coverage_csv_header_and_short_rows_fail_closed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.csv"
            path.write_text("surface,disposition\nlaunch,mapped\n", encoding="utf-8")
            errors = validate_reference_coverage(path, {"launch": {}}, {})
            self.assertTrue(any("expected header" in error for error in errors))
            path.write_text(
                "surface,disposition,page,section,evidence_ids,reason\nlaunch,mapped\n",
                encoding="utf-8",
            )
            errors = validate_reference_coverage(path, {"launch": {}}, {})
        self.assertTrue(any("expected string fields" in error for error in errors))

    def test_schemas_publish_complete_record_contracts(self):
        evidence_schema = json.loads(
            (ROOT / "research/schemas/reference-evidence.schema.json").read_text()
        )
        coverage_schema = json.loads(
            (ROOT / "research/schemas/reference-coverage.schema.json").read_text()
        )
        record = evidence_schema["properties"]["evidence"]["items"]
        self.assertEqual(record["required"], [
            "evidence_id", "snapshot_id", "path", "start_line", "end_line",
            "state", "claim", "source_ids", "verification_condition",
        ])
        self.assertEqual(record["properties"]["source_ids"]["minItems"], 1)
        self.assertTrue(record["properties"]["source_ids"]["uniqueItems"])
        self.assertIn("allOf", coverage_schema)
