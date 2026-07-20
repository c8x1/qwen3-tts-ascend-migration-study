import collections
import contextlib
import copy
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from scripts import phase2_contracts as contracts
from scripts.phase2_contracts import (
    Snapshot,
    _materialized_digest,
    load_snapshot_registry,
    load_source_index_schema,
    validate_snapshot_registry,
    validate_source_index,
)
from scripts import validate_phase2 as validate_phase2_cli
from scripts.validate_phase2 import validate_indexes


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research" / "source-snapshots.json"


def valid_minimal_index(*, snapshot):
    data = {
        "schema_version": 1,
        "snapshot": {
            "snapshot_id": snapshot.snapshot_id,
            "project": snapshot.project,
            "role": snapshot.role,
            "revision": snapshot.revision,
            "acquisition_kind": snapshot.acquisition_kind,
            "content_id": snapshot.content_id,
        },
        "indexer_version": "1.0",
        "files": [
            {
                "path": "pkg/module.py",
                "bytes": 12,
                "sha256": "c" * 64,
                "kind": "python",
                "line_count": 8,
            }
        ],
        "symbols": [
            {
                "id": "pkg/module.py:Widget.run:2",
                "path": "pkg/module.py",
                "qualname": "Widget.run",
                "name": "run",
                "kind": "method",
                "line": 2,
                "end_line": 5,
            }
        ],
        "configs": [
            {
                "id": "pkg/module.py:batch_size:7",
                "path": "pkg/module.py",
                "key": "batch_size",
                "owner": "Widget",
                "kind": "python-assignment",
                "line": 7,
            }
        ],
        "content_digest": "",
    }
    refresh_materialized_digest(data)
    return data


def refresh_materialized_digest(data):
    data["content_digest"] = _materialized_digest(data)


def registry():
    return load_snapshot_registry(ROOT / "research/source-snapshots.json")


def target_index():
    return json.loads(
        (ROOT / "research/indexes/qwen3-tts-022e286b.json").read_text(
            encoding="utf-8"
        )
    )


def ledger_ids():
    with (ROOT / "research/source-ledger.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        return {row["source_id"] for row in csv.DictReader(handle)}


def valid_evidence_document():
    def source_record(evidence_id, path):
        return {
            "evidence_id": evidence_id,
            "snapshot_id": "qwen3-tts-022e286b",
            "path": path,
            "start_line": 1,
            "end_line": 2,
            "state": "verified",
            "claim": "claim",
            "quote": "",
            "source_ids": ["SRC-001"],
            "decision_refs": [],
        }

    return {
        "schema_version": 1,
        "records": [
            source_record("E-1", "pyproject.toml"),
            source_record("E-2", "LICENSE"),
            {
                "evidence_id": "E-3",
                "snapshot_id": None,
                "path": None,
                "start_line": None,
                "end_line": None,
                "state": "inference",
                "claim": "decision",
                "quote": "",
                "source_ids": ["SRC-019"],
                "decision_refs": ["research/reference-selection-proposal.md"],
            },
        ],
    }


class SnapshotRegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_committed_registry_has_the_approved_snapshots(self):
        self.assertEqual([], validate_snapshot_registry(self.data))
        registry = load_snapshot_registry(REGISTRY_PATH)
        self.assertEqual(
            {
                "qwen3-tts-022e286b",
                "mindspeed-mm-0edd553e",
                "mindspeed-llm-434baff7",
                "moss-tts-ad99ec5f",
            },
            set(registry),
        )
        self.assertEqual(
            {
                "qwen3-tts-022e286b": "git-sparse-checkout",
                "mindspeed-mm-0edd553e": "codeload-archive",
                "mindspeed-llm-434baff7": "codeload-archive",
                "moss-tts-ad99ec5f": "git-sparse-checkout",
            },
            {
                snapshot_id: snapshot.acquisition_kind
                for snapshot_id, snapshot in registry.items()
            },
        )
        self.assertEqual(
            3270,
            sum(snapshot.materialized_file_count for snapshot in registry.values()),
        )
        self.assertEqual("official-target", registry["qwen3-tts-022e286b"].role)
        self.assertEqual(35, registry["qwen3-tts-022e286b"].materialized_file_count)
        self.assertEqual(
            (".github/.DS_Store", "assets/Qwen3_TTS.pdf"),
            registry["qwen3-tts-022e286b"].excluded_paths,
        )
        self.assertEqual("main-reference", registry["mindspeed-mm-0edd553e"].role)
        self.assertEqual(1405, registry["mindspeed-mm-0edd553e"].materialized_file_count)
        self.assertEqual(1664, registry["mindspeed-llm-434baff7"].materialized_file_count)
        moss = registry["moss-tts-ad99ec5f"]
        self.assertEqual(166, moss.materialized_file_count)
        self.assertEqual(18, len(moss.excluded_paths))
        self.assertEqual(
            "assets/audio/reference_02_s1.wav", moss.excluded_paths[0]
        )
        self.assertEqual(
            (
                {
                    "path": "moss_audio_tokenizer",
                    "revision": "56776e867cb38446fa4bc00d0aceccab5001b008",
                    "initialized": False,
                },
            ),
            moss.gitlinks,
        )
        with self.assertRaises(FrozenInstanceError):
            moss.project = "changed"

    def test_registry_rejects_unknown_local_path_and_archive_git_claim(self):
        local_path = copy.deepcopy(self.data)
        local_path["snapshots"][1]["local_path"] = "/tmp/source"
        self.assertIn(
            "snapshots[1]: unknown field local_path",
            validate_snapshot_registry(local_path),
        )

        wrong_kind = copy.deepcopy(self.data)
        wrong_kind["snapshots"][1]["acquisition_kind"] = "git-sparse-checkout"
        self.assertIn(
            "snapshots[1].acquisition_kind: expected codeload-archive",
            validate_snapshot_registry(wrong_kind),
        )

        git_claim = copy.deepcopy(self.data)
        git_claim["snapshots"][1]["content_id"] = "git-tree:" + "a" * 40
        self.assertIn(
            "snapshots[1].content_id: expected "
            "archive-sha256:1b52f9a6a8e3536f02a7a06ed01cc4d00dafc57617783ca2a04d0250b670ba15",
            validate_snapshot_registry(git_claim),
        )

    def test_registry_rejects_unknown_incomplete_identity_and_bad_paths(self):
        unknown = copy.deepcopy(self.data)
        unknown["snapshots"][0]["snapshot_id"] = "unknown-snapshot"
        errors = validate_snapshot_registry(unknown)
        self.assertIn(
            "snapshots[0].snapshot_id: unapproved unknown-snapshot", errors
        )
        self.assertTrue(
            any(error.startswith("registry.snapshots: expected approved IDs") for error in errors)
        )

        incomplete = copy.deepcopy(self.data)
        del incomplete["snapshots"][0]["project"]
        self.assertIn(
            "snapshots[0]: missing field project",
            validate_snapshot_registry(incomplete),
        )

        for bad_path in ("/absolute", "../escape", "dir\\file", "a/../b"):
            with self.subTest(path=bad_path):
                mutated = copy.deepcopy(self.data)
                mutated["snapshots"][0]["excluded"]["paths"] = [bad_path]
                self.assertTrue(
                    any("expected relative POSIX path" in error for error in validate_snapshot_registry(mutated))
                )

    def test_registry_preserves_stable_regression_errors(self):
        mutated = copy.deepcopy(self.data)
        mutated["snapshots"][0]["snapshot_id"] = "unknown-snapshot"
        mutated["snapshots"][1]["project"] = ""
        mutated["snapshots"][2]["materialized_file_count"] = -1
        mutated["snapshots"][3]["excluded"]["paths"] = [
            "../escape",
            "../escape",
        ]

        errors = validate_snapshot_registry(mutated)
        self.assertIn(
            "snapshots[0].snapshot_id: unapproved unknown-snapshot", errors
        )
        self.assertIn(
            "snapshots[1].project: expected non-empty string", errors
        )
        self.assertIn(
            "snapshots[2].materialized_file_count: expected nonnegative integer",
            errors,
        )
        self.assertIn("snapshots[3].excluded.paths: duplicate path", errors)
        self.assertIn(
            "snapshots[3].excluded.paths: expected relative POSIX path ../escape",
            errors,
        )
        self.assertTrue(
            any(
                error.startswith("registry.snapshots: expected approved IDs")
                for error in errors
            )
        )

    def test_registry_validation_is_total_for_malformed_roots_and_rows(self):
        cases = [None, [], "registry", 1, True]
        for value in cases:
            with self.subTest(root=value):
                self.assertEqual(["registry: expected object"], validate_snapshot_registry(value))

        wrong_version = copy.deepcopy(self.data)
        wrong_version["schema_version"] = 2
        self.assertIn(
            "registry.schema_version: expected 1",
            validate_snapshot_registry(wrong_version),
        )

        for row in (None, [], "snapshot", 7, True):
            with self.subTest(row=row):
                mutated = copy.deepcopy(self.data)
                mutated["snapshots"][0] = row
                errors = validate_snapshot_registry(mutated)
                self.assertIn("snapshots[0]: expected object", errors)

        malformed = copy.deepcopy(self.data)
        malformed["snapshots"] = None
        self.assertIn(
            "registry.snapshots: expected array",
            validate_snapshot_registry(malformed),
        )

    def test_loader_rejects_invalid_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text('{"schema_version": 1, "snapshots": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected approved IDs"):
                load_snapshot_registry(path)


class SourceIndexContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = Snapshot(
            snapshot_id="fixture-snapshot",
            project="Example/Project",
            role="fixture",
            revision="a" * 40,
            acquisition_kind="git-sparse-checkout",
            content_id="git-tree:" + "b" * 40,
            materialized_file_count=1,
            blob_url_template="https://example.test/blob/{path}#L{start}-L{end}",
            excluded_paths=(),
            gitlinks=(),
        )
        self.registry = {self.snapshot.snapshot_id: self.snapshot}

    def valid_index(self):
        return valid_minimal_index(snapshot=self.snapshot)

    @staticmethod
    def refresh_digest(data):
        refresh_materialized_digest(data)

    def errors_after(self, mutate, *, refresh=True):
        data = self.valid_index()
        mutate(data)
        if refresh:
            self.refresh_digest(data)
        return validate_source_index(data, self.registry)

    def test_schema_is_cached_and_has_required_public_identity(self):
        schema = load_source_index_schema()
        self.assertIs(schema, load_source_index_schema())
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertEqual("https://c8x1.github.io/schemas/source-index-v1.json", schema["$id"])
        self.assertEqual("Qwen3-TTS Ascend source index v1", schema["title"])
        property_names = set()

        def collect_property_names(node):
            if isinstance(node, dict):
                properties = node.get("properties")
                if isinstance(properties, dict):
                    property_names.update(properties)
                for value in node.values():
                    collect_property_names(value)
            elif isinstance(node, list):
                for value in node:
                    collect_property_names(value)

        collect_property_names(schema)
        for forbidden in ("source_root", "body", "source", "text", "generated_at"):
            self.assertNotIn(forbidden, property_names)

    def test_valid_minimal_index_and_canonical_digest(self):
        data = self.valid_index()
        self.assertEqual([], validate_source_index(data, self.registry))
        clone = copy.deepcopy(data)
        clone["content_digest"] = "ignored by digest"
        self.assertEqual(data["content_digest"], _materialized_digest(clone))

    def test_recursive_schema_validation_is_total(self):
        cases = [
            (lambda d: d.__setitem__("snapshot", []), "index.snapshot: expected object"),
            (lambda d: d["snapshot"].__setitem__("extra", 1), "index.snapshot: unknown field extra"),
            (lambda d: d["snapshot"].pop("project"), "index.snapshot: missing field project"),
            (lambda d: d.__setitem__("files", {}), "index.files: expected array"),
            (lambda d: d.__setitem__("files", [None]), "index.files[0]: expected object"),
            (lambda d: d["symbols"][0].__setitem__("line", "2"), "index.symbols[0].line: expected integer"),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.errors_after(mutate))

    def test_schema_unknown_missing_type_enum_sha_and_minimum_errors(self):
        cases = [
            (lambda d: d.__setitem__("extra", 1), "index: unknown field extra"),
            (lambda d: d.pop("configs"), "index: missing field configs"),
            (lambda d: d.__setitem__("schema_version", "1"), "index.schema_version: expected integer"),
            (lambda d: d["files"][0].__setitem__("kind", "source"), "index.files[0].kind: expected one of"),
            (lambda d: d["files"][0].__setitem__("sha256", "ABC"), "index.files[0].sha256: does not match pattern"),
            (lambda d: d["files"][0].__setitem__("bytes", -1), "index.files[0].bytes: expected minimum 0"),
            (lambda d: d["symbols"][0].__setitem__("line", 0), "index.symbols[0].line: expected minimum 1"),
            (lambda d: d["files"][0].__setitem__("line_count", "8"), "index.files[0].line_count: expected exactly one allowed shape"),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                self.assertTrue(any(error.startswith(expected) for error in self.errors_after(mutate)))

    def test_line_count_rules(self):
        errors = self.errors_after(
            lambda d: d["files"][0].__setitem__("line_count", None)
        )
        self.assertIn("index.files[0].line_count: nonbinary files require an integer", errors)

        def binary_with_lines(data):
            data["files"][0]["kind"] = "binary"
            data["files"][0]["line_count"] = 8

        self.assertIn(
            "index.files[0].line_count: binary files require null",
            self.errors_after(binary_with_lines),
        )

    def test_rejects_posix_windows_and_unc_absolute_paths(self):
        for path in ("/etc/passwd", "C:\\secret\\file.py", "\\\\server\\share\\file.py"):
            with self.subTest(path=path):
                errors = self.errors_after(
                    lambda data, path=path: data["files"][0].__setitem__("path", path)
                )
                self.assertIn("index.files[0].path: absolute path forbidden", errors)

        errors = self.errors_after(
            lambda data: data["configs"][0].__setitem__(
                "owner", r"C:\Users\alice\project"
            )
        )
        self.assertIn("index.configs[0].owner: absolute path forbidden", errors)

    def test_rejects_reversed_symbol_range_and_missing_or_binary_owner(self):
        def reverse(data):
            data["symbols"][0]["line"] = 6
            data["symbols"][0]["end_line"] = 3
            data["symbols"][0]["id"] = "pkg/module.py:Widget.run:6"

        self.assertIn(
            "index.symbols[0]: line exceeds end_line",
            self.errors_after(reverse),
        )

        missing = self.errors_after(
            lambda d: d["symbols"][0].__setitem__("path", "missing.py")
        )
        self.assertIn("index.symbols[0].path: not in files", missing)

        def binary_owner(data):
            data["files"][0]["kind"] = "binary"
            data["files"][0]["line_count"] = None

        binary_errors = self.errors_after(binary_owner)
        self.assertIn(
            "index.symbols[0].line: exceeds file line_count", binary_errors
        )
        self.assertIn(
            "index.configs[0].line: exceeds file line_count", binary_errors
        )

    def test_sort_and_duplicate_rules(self):
        def unsorted_files(data):
            row = copy.deepcopy(data["files"][0])
            row["path"] = "a.py"
            data["files"].append(row)

        self.assertIn("index.files: rows must be sorted by path", self.errors_after(unsorted_files))

        def duplicate_file(data):
            data["files"].append(copy.deepcopy(data["files"][0]))

        self.assertIn("index.files: duplicate path pkg/module.py", self.errors_after(duplicate_file))

        for key in ("symbols", "configs"):
            def duplicate_id(data, key=key):
                data[key].append(copy.deepcopy(data[key][0]))

            with self.subTest(key=key):
                errors = self.errors_after(duplicate_id)
                singular = "symbol" if key == "symbols" else "config"
                self.assertTrue(any(error.startswith(f"index.{key}: duplicate id ") for error in errors))
                self.assertNotIn(f"unused-{singular}", errors)

        def unsorted_symbols(data):
            row = copy.deepcopy(data["symbols"][0])
            row["id"] = "a.py:a:1"
            row["path"] = "pkg/module.py"
            row["qualname"] = "a"
            row["name"] = "a"
            row["line"] = 1
            row["end_line"] = 1
            data["symbols"].append(row)

        self.assertIn("index.symbols: rows must be sorted by id", self.errors_after(unsorted_symbols))

    def test_identity_row_ids_and_owner_bounds(self):
        self.assertIn(
            "index.snapshot.project: expected Example/Project",
            self.errors_after(lambda d: d["snapshot"].__setitem__("project", "Other/Project")),
        )
        self.assertIn(
            "index.snapshot.snapshot_id: unknown snapshot missing",
            self.errors_after(lambda d: d["snapshot"].__setitem__("snapshot_id", "missing")),
        )
        self.assertIn(
            "index.symbols[0].id: expected pkg/module.py:Widget.run:2",
            self.errors_after(lambda d: d["symbols"][0].__setitem__("id", "wrong")),
        )
        self.assertIn(
            "index.configs[0].id: expected pkg/module.py:batch_size:7",
            self.errors_after(lambda d: d["configs"][0].__setitem__("id", "wrong")),
        )
        self.assertIn(
            "index.configs[0].line: exceeds file line_count",
            self.errors_after(lambda d: d["configs"][0].__setitem__("line", 9)),
        )
        self.assertIn(
            "index.symbols[0].end_line: exceeds file line_count",
            self.errors_after(lambda d: d["symbols"][0].__setitem__("end_line", 9)),
        )
        self.assertIn(
            "index.symbols[0].line: exceeds file line_count",
            self.errors_after(lambda d: d["symbols"][0].__setitem__("line", 9)),
        )

    def test_digest_and_recursive_forbidden_fields(self):
        data = self.valid_index()
        data["files"][0]["bytes"] += 1
        self.assertIn("index.content_digest: does not match materialized content", validate_source_index(data, self.registry))

        for forbidden in ("source_root", "body", "source", "text", "generated_at", "local_path"):
            with self.subTest(forbidden=forbidden):
                value = "print(1)" if forbidden == "body" else "secret"
                errors = self.errors_after(
                    lambda d, forbidden=forbidden, value=value: d["files"][0].__setitem__(forbidden, value)
                )
                self.assertTrue(any(f"forbidden field {forbidden}" in error for error in errors))
                if forbidden == "body":
                    self.assertIn("index.files[0]: unknown field body", errors)

        errors = self.errors_after(
            lambda d: d.__setitem__(
                "extra", {"nested": {"local_path": "relative/source"}}
            )
        )
        self.assertIn("index.extra.nested: forbidden field local_path", errors)

    def test_malformed_root_never_raises(self):
        for value in (None, [], "index", 1, True):
            with self.subTest(value=value):
                self.assertEqual(["index: expected object"], validate_source_index(value, self.registry))


class SourceIndexContractTest(unittest.TestCase):
    def test_index_rejects_absolute_path_after_schema_validation(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        data = valid_minimal_index(snapshot=registry["qwen3-tts-022e286b"])
        data["files"][0]["path"] = "/Users/me/source.py"
        data["symbols"][0]["path"] = "/Users/me/source.py"
        data["symbols"][0]["id"] = "/Users/me/source.py:f:1"
        refresh_materialized_digest(data)
        errors = validate_source_index(data, registry)
        self.assertTrue(any("absolute path forbidden" in error for error in errors))

    def test_index_rejects_unknown_body_at_schema_layer(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        data = valid_minimal_index(snapshot=registry["qwen3-tts-022e286b"])
        data["files"][0]["body"] = "print(1)"
        errors = validate_source_index(data, registry)
        self.assertIn("index.files[0]: unknown field body", errors)

    def test_tracked_indexes_match_registry_counts_and_revisions(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        for snapshot_id, snapshot in registry.items():
            data = json.loads((ROOT / "research/indexes" / f"{snapshot_id}.json").read_text())
            self.assertEqual(data["snapshot"]["revision"], snapshot.revision)
            self.assertEqual(len(data["files"]), snapshot.materialized_file_count)
            self.assertEqual(validate_source_index(data, registry), [])

    def test_real_indexes_keep_duplicate_qualnames_but_unique_line_ids(self):
        expected_groups = {"mindspeed-mm-0edd553e": 10, "moss-tts-ad99ec5f": 1}
        for snapshot_id, expected in expected_groups.items():
            data = json.loads((ROOT / "research/indexes" / f"{snapshot_id}.json").read_text())
            pairs = collections.Counter((row["path"], row["qualname"]) for row in data["symbols"])
            self.assertEqual(sum(count > 1 for count in pairs.values()), expected)
            self.assertEqual(len({row["id"] for row in data["symbols"]}), len(data["symbols"]))

    def test_validator_rejects_unencodable_metadata_without_raising(self):
        registry = load_snapshot_registry(ROOT / "research/source-snapshots.json")
        snapshot = registry["qwen3-tts-022e286b"]
        mutations = {
            "unknown field": lambda data: data.__setitem__("extra", "\ud800"),
            "schema string": lambda data: data["snapshot"].__setitem__(
                "project", "\ud800"
            ),
        }
        for case, mutate in mutations.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "research/indexes").mkdir(parents=True)
                (root / "research/source-snapshots.json").write_text(
                    (ROOT / "research/source-snapshots.json").read_text(
                        encoding="utf-8"
                    ),
                    encoding="utf-8",
                )
                data = valid_minimal_index(snapshot=snapshot)
                mutate(data)
                index_path = (
                    root / "research/indexes/qwen3-tts-022e286b.json"
                )
                index_path.write_text(
                    json.dumps(data, ensure_ascii=True), encoding="utf-8"
                )

                errors = validate_indexes(root)

                self.assertIn(
                    "qwen3-tts-022e286b.json: content digest input is not "
                    "UTF-8 encodable",
                    errors,
                )
                self.assertTrue(all("\n" not in error for error in errors))


class TargetCoverageTest(unittest.TestCase):
    def setUp(self):
        # Keep the first TDD failure tied to the absent contract artifacts rather
        # than to target APIs that do not exist before the GREEN implementation.
        (ROOT / "research/target-coverage.csv").read_bytes()
        (ROOT / "research/target-evidence.json").read_bytes()

    def load_evidence(self):
        return contracts.load_evidence(ROOT / "research/target-evidence.json")

    def test_every_target_file_has_exactly_one_disposition(self):
        errors = contracts.validate_target_coverage(
            target_index(), ROOT / "research/target-coverage.csv"
        )
        self.assertEqual(errors, [])

        with (ROOT / "research/target-coverage.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(
            list(rows[0]),
            ["path", "disposition", "page", "section", "evidence_ids", "reason"],
        )
        self.assertEqual(len(rows), 35)
        self.assertEqual(
            [row["path"] for row in rows],
            [row["path"] for row in target_index()["files"]],
        )

    def test_default_and_explicit_evidence_coverage_calls_are_identical(self):
        evidence = self.load_evidence()
        with (ROOT / "research/target-coverage.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["evidence_ids"] = "UNKNOWN-EVIDENCE"
        default_errors = contracts.validate_target_coverage(target_index(), rows)
        explicit_errors = contracts.validate_target_coverage(
            target_index(), rows, evidence=evidence
        )
        self.assertEqual(default_errors, explicit_errors)
        self.assertIn(
            "coverage[0] .github/ISSUE_TEMPLATE/bug_report.yml: unknown evidence UNKNOWN-EVIDENCE",
            default_errors,
        )

    def test_coverage_catalog_missing_fields_returns_error_without_raising(self):
        index = {"files": [{"path": "pkg.py"}]}
        rows = [
            {
                "path": "pkg.py",
                "disposition": "mapped",
                "evidence_ids": "",
                "reason": "",
            }
        ]
        self.assertEqual(
            ["coverage[0] pkg.py: page and section required"],
            contracts.validate_target_coverage(
                index, rows, evidence={}, page_catalog=[]
            ),
        )

    def test_coverage_programmatic_non_mapping_rows_return_stable_errors(self):
        index = {"files": [{"path": "pkg.py"}]}
        for malformed in (None, [], "row", 1, True):
            with self.subTest(malformed=malformed):
                errors = contracts.validate_target_coverage(
                    index, [malformed], evidence={}
                )
                self.assertIn("coverage[0]: expected object", errors)

    def test_coverage_short_csv_and_header_errors_are_total_and_stable(self):
        index = {"files": [{"path": "pkg.py"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.csv"
            path.write_text(
                "path,disposition,page,section,evidence_ids,reason\n"
                "pkg.py,mapped\n",
                encoding="utf-8",
            )
            errors = contracts.validate_target_coverage(
                index, path, evidence={}
            )
            for field in ("page", "section", "evidence_ids", "reason"):
                self.assertIn(
                    f"coverage[0] pkg.py.{field}: expected string", errors
                )
            self.assertIn(
                "coverage[0] pkg.py: page and section required", errors
            )

            path.write_text(
                "path,disposition\npkg.py,mapped\n", encoding="utf-8"
            )
            self.assertIn(
                "target coverage: expected header "
                "path,disposition,page,section,evidence_ids,reason",
                contracts.validate_target_coverage(
                    index, path, evidence={}
                ),
            )

    def test_page_catalog_malformed_matrix_is_total_and_aggregates(self):
        index = {"files": [{"path": "pkg.py"}]}
        rows = [
            {
                "path": "pkg.py",
                "disposition": "mapped",
                "page": "page.html",
                "section": "sec",
                "evidence_ids": "",
                "reason": "",
            }
        ]
        cases = [
            ({}, "page_catalog: expected array"),
            ("catalog", "page_catalog: expected array"),
            (1, "page_catalog: expected array"),
            (True, "page_catalog: expected array"),
            ([None], "page_catalog[0]: expected object"),
            (
                [{"sections": []}],
                "page_catalog[0]: missing field slug",
            ),
            (
                [{"slug": "page.html"}],
                "page_catalog[0]: missing field sections",
            ),
            (
                [{"slug": None, "sections": []}],
                "page_catalog[0].slug: expected string",
            ),
            (
                [{"slug": "page.html", "sections": None}],
                "page_catalog[0].sections: expected array",
            ),
            (
                [{"slug": "page.html", "sections": [None]}],
                "page_catalog[0].sections[0]: expected object",
            ),
            (
                [{"slug": "page.html", "sections": [{}]}],
                "page_catalog[0].sections[0]: missing field id",
            ),
            (
                [{"slug": "page.html", "sections": [{"id": None}]}],
                "page_catalog[0].sections[0].id: expected string",
            ),
        ]
        for malformed, expected in cases:
            with self.subTest(expected=expected):
                errors = contracts.validate_target_coverage(
                    index, rows, evidence={}, page_catalog=malformed
                )
                self.assertIn(expected, errors)
                self.assertIn(
                    "coverage[0] pkg.py: missing section page.html#sec",
                    errors,
                )

        self.assertEqual(
            [],
            contracts.validate_target_coverage(
                index,
                rows,
                evidence={},
                page_catalog=[
                    {"slug": "page.html", "sections": [{"id": "sec"}]}
                ],
            ),
        )

    def test_evidence_has_four_states_bounded_quotes_and_tuple_arrays(self):
        evidence = self.load_evidence()
        self.assertEqual(
            {row.state for row in evidence.values()},
            {"verified", "project_claim", "inference", "pending_hardware"},
        )
        self.assertTrue(
            all(
                len(row.quote) <= 240 and row.quote.count("\n") < 8
                for row in evidence.values()
            )
        )
        self.assertTrue(all(isinstance(row.source_ids, tuple) for row in evidence.values()))
        self.assertTrue(
            all(isinstance(row.decision_refs, tuple) for row in evidence.values())
        )
        with self.assertRaises(FrozenInstanceError):
            next(iter(evidence.values())).claim = "changed"

    def test_evidence_ranges_exist_in_index_and_quotes_match_fixed_lines(self):
        excerpts = json.loads(
            (
                ROOT / "tests/fixtures/evidence/qwen3-tts-excerpts.json"
            ).read_text(encoding="utf-8")
        )
        evidence = self.load_evidence()
        quoted = {
            evidence_id for evidence_id, row in evidence.items() if row.quote
        }
        self.assertEqual(quoted, set(excerpts))
        self.assertEqual(len(quoted), 4)
        for evidence_id, lines in excerpts.items():
            row = evidence[evidence_id]
            self.assertTrue(row.quote)
            self.assertEqual(lines["path"], row.path)
            self.assertEqual(
                [lines["start_line"], lines["end_line"]],
                [row.start_line, row.end_line],
            )
            self.assertEqual(
                len(lines["lines"]), lines["end_line"] - lines["start_line"] + 1
            )
            self.assertIn(row.quote, "\n".join(lines["lines"]))

    def test_all_source_ids_exist_in_phase1_ledger(self):
        known = ledger_ids()
        for row in self.load_evidence().values():
            self.assertTrue(row.source_ids)
            self.assertLessEqual(set(row.source_ids), known)

    def test_evidence_rejects_reversed_range_wrong_snapshot_and_bad_decision_ref(self):
        data = valid_evidence_document()
        data["records"][0].update({"start_line": 8, "end_line": 7})
        data["records"][1]["snapshot_id"] = "moss-tts-ad99ec5f"
        data["records"][2]["decision_refs"] = ["/tmp/decision.md"]
        errors = contracts.validate_evidence(
            data, registry(), target_index(), ledger_ids(), ROOT
        )
        self.assertIn("evidence.records[0]: start_line exceeds end_line", errors)
        self.assertIn(
            "evidence.records[1].snapshot_id: expected target snapshot qwen3-tts-022e286b",
            errors,
        )
        self.assertIn(
            "evidence.records[2].decision_refs: disallowed /tmp/decision.md",
            errors,
        )

    def test_evidence_schema_rejects_container_and_list_contracts(self):
        mutations = [
            (
                lambda row: row.update(source_ids=[]),
                "evidence.records[0].source_ids: fewer than 1 items",
            ),
            (
                lambda row: row.update(source_ids=["SRC-001", "SRC-001"]),
                "evidence.records[0].source_ids: duplicate item",
            ),
            (
                lambda row: row.update(source_ids=["source-1"]),
                "evidence.records[0].source_ids[0]: does not match pattern ^SRC-[0-9]{3}$",
            ),
            (
                lambda row: row.update(quote="x" * 241),
                "evidence.records[0].quote: longer than 240",
            ),
            (
                lambda row: row.update(claim=""),
                "evidence.records[0].claim: shorter than 1",
            ),
            (
                lambda row: row.update(claim="x" * 501),
                "evidence.records[0].claim: longer than 500",
            ),
            (
                lambda row: row.update(start_line=None),
                "evidence.records[0]: expected exactly one oneOf branch",
            ),
            (
                lambda row: row.update(extra=True),
                "evidence.records[0]: unknown field extra",
            ),
            (
                lambda row: row.update(
                    decision_refs=[
                        "research/reference-selection-proposal.md",
                        "research/reference-selection-proposal.md",
                    ]
                ),
                "evidence.records[0].decision_refs: duplicate item",
            ),
            (
                lambda row: row.update(decision_refs=[""]),
                "evidence.records[0].decision_refs[0]: shorter than 1",
            ),
        ]
        for mutate, expected in mutations:
            with self.subTest(expected=expected):
                data = valid_evidence_document()
                mutate(data["records"][0])
                self.assertIn(
                    expected,
                    contracts.validate_evidence(
                        data, registry(), target_index(), ledger_ids(), ROOT
                    ),
                )

    def test_evidence_schema_validation_is_total_for_malformed_values(self):
        for malformed in (None, [], "evidence", 1, True):
            with self.subTest(malformed=malformed):
                self.assertEqual(
                    ["evidence: expected object"],
                    contracts.validate_evidence(
                        malformed, registry(), target_index(), ledger_ids(), ROOT
                    ),
                )

        cases = [
            (
                lambda data: data.__setitem__("records", {}),
                "evidence.records: expected array",
            ),
            (
                lambda data: data["records"].__setitem__(0, None),
                "evidence.records[0]: expected object",
            ),
            (
                lambda data: data["records"][0].update(evidence_id="bad id"),
                "evidence.records[0].evidence_id: does not match pattern ^[A-Z0-9-]+$",
            ),
            (
                lambda data: data["records"][0].update(start_line=0),
                "evidence.records[0].start_line: expected minimum 1",
            ),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                data = valid_evidence_document()
                mutate(data)
                self.assertIn(
                    expected,
                    contracts.validate_evidence(
                        data, registry(), target_index(), ledger_ids(), ROOT
                    ),
                )

    def test_evidence_semantics_cover_source_file_and_ledger_shapes(self):
        unknown_source = valid_evidence_document()
        unknown_source["records"][0]["source_ids"] = ["SRC-999"]
        self.assertIn(
            "evidence.records[0].source_ids: unknown SRC-999",
            contracts.validate_evidence(
                unknown_source, registry(), target_index(), ledger_ids(), ROOT
            ),
        )

        missing_path = valid_evidence_document()
        missing_path["records"][0]["path"] = "missing.py"
        self.assertIn(
            "evidence.records[0].path: not in target index",
            contracts.validate_evidence(
                missing_path, registry(), target_index(), ledger_ids(), ROOT
            ),
        )

        text_file_only = valid_evidence_document()
        text_file_only["records"][0].update(start_line=None, end_line=None)
        self.assertIn(
            "evidence.records[0].path: file-only evidence requires indexed binary",
            contracts.validate_evidence(
                text_file_only, registry(), target_index(), ledger_ids(), ROOT
            ),
        )

        binary_range = valid_evidence_document()
        binary_range["records"][0]["path"] = (
            "qwen_tts/core/tokenizer_25hz/vq/assets/mel_filters.npz"
        )
        self.assertIn(
            "evidence.records[0].path: binary file cannot have line range",
            contracts.validate_evidence(
                binary_range, registry(), target_index(), ledger_ids(), ROOT
            ),
        )

        too_long = valid_evidence_document()
        too_long["records"][0]["end_line"] = 47
        self.assertIn(
            "evidence.records[0].end_line: exceeds pyproject.toml line_count",
            contracts.validate_evidence(
                too_long, registry(), target_index(), ledger_ids(), ROOT
            ),
        )

        with tempfile.TemporaryDirectory() as directory:
            self.assertIn(
                "evidence.records[2].decision_refs: missing research/reference-selection-proposal.md",
                contracts.validate_evidence(
                    valid_evidence_document(),
                    registry(),
                    target_index(),
                    ledger_ids(),
                    Path(directory),
                ),
            )

    def test_fixed_urls_anchor_text_not_binary_and_ledger_has_no_source_url(self):
        evidence = self.load_evidence()
        snapshots = registry()
        text_url = contracts.fixed_url(evidence["TGT-API-001"], snapshots)
        self.assertEqual(
            text_url,
            "https://github.com/QwenLM/Qwen3-TTS/blob/"
            "022e286b98fbec7e1e916cb940cdf532cd9f488e/"
            "qwen_tts/inference/qwen3_tts_model.py#L83-L121",
        )
        binary_url = contracts.fixed_url(evidence["TGT-TOK25-014"], snapshots)
        self.assertEqual(
            binary_url,
            "https://github.com/QwenLM/Qwen3-TTS/blob/"
            "022e286b98fbec7e1e916cb940cdf532cd9f488e/"
            "qwen_tts/core/tokenizer_25hz/vq/assets/mel_filters.npz",
        )
        self.assertIsNone(contracts.fixed_url(evidence["PH1-ROLE-MM"], snapshots))

    def test_phase2_cli_preserves_indexes_only_and_reports_dynamic_counts(self):
        indexes = subprocess.run(
            ["python3", "scripts/validate_phase2.py", "--indexes-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(indexes.returncode, 0, indexes.stdout + indexes.stderr)
        self.assertEqual(
            indexes.stdout,
            "validated 4 source indexes: 3270 files; no absolute paths or source bodies\n",
        )

        combined = subprocess.run(
            ["python3", "scripts/validate_phase2.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(combined.returncode, 0, combined.stdout + combined.stderr)
        match = re.fullmatch(
            r"validated Phase 2 data: 4 indexes, (\d+) evidence records, "
            r"35 target coverage rows, 0 omissions\n",
            combined.stdout,
        )
        self.assertIsNotNone(match, combined.stdout)
        self.assertEqual(int(match.group(1)), len(self.load_evidence()))

    def test_phase2_default_stops_when_index_validation_fails(self):
        output = io.StringIO()
        with (
            patch.object(
                validate_phase2_cli,
                "validate_indexes",
                return_value=["qwen3-tts-022e286b.json: index.files: expected array"],
            ),
            patch.object(
                validate_phase2_cli,
                "load_evidence",
                side_effect=AssertionError("evidence validation must not run"),
            ) as evidence_loader,
            patch.object(sys, "argv", ["validate_phase2.py"]),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(1, validate_phase2_cli.main())
        evidence_loader.assert_not_called()
        self.assertEqual(
            "qwen3-tts-022e286b.json: index.files: expected array\n",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
