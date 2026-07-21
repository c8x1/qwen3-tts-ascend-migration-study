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
        errors = validate_reference_coverage(rows, {"launch", "checkpoint"}, evidence)
        self.assertTrue(any("duplicate surface launch" in error for error in errors))
        self.assertTrue(any("missing surface checkpoint" in error for error in errors))
        self.assertTrue(any("unknown evidence unknown" in error for error in errors))
