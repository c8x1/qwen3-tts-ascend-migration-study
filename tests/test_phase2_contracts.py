import copy
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from scripts.phase2_contracts import (
    Snapshot,
    _materialized_digest,
    load_snapshot_registry,
    load_source_index_schema,
    validate_snapshot_registry,
    validate_source_index,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research" / "source-snapshots.json"


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
        data = {
            "schema_version": 1,
            "snapshot": {
                "snapshot_id": self.snapshot.snapshot_id,
                "project": self.snapshot.project,
                "role": self.snapshot.role,
                "revision": self.snapshot.revision,
                "acquisition_kind": self.snapshot.acquisition_kind,
                "content_id": self.snapshot.content_id,
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
        self.refresh_digest(data)
        return data

    @staticmethod
    def refresh_digest(data):
        data["content_digest"] = _materialized_digest(data)

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
        self.assertIn("index.symbols[0].path: binary owner has no line count", binary_errors)
        self.assertIn("index.configs[0].path: binary owner has no line count", binary_errors)

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
                errors = self.errors_after(
                    lambda d, forbidden=forbidden: d["files"][0].__setitem__(forbidden, "secret")
                )
                self.assertTrue(any(f"forbidden field {forbidden}" in error for error in errors))

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


if __name__ == "__main__":
    unittest.main()
