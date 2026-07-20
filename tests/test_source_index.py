import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.phase2_contracts import Snapshot, validate_source_index
from scripts.source_index import build_index, file_kind, write_canonical_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/source-index/source"
SNAPSHOT = Snapshot("fixture", "Fixture/Source", "test", "a" * 40, "codeload-archive", "fixture:1", 5, "https://example.invalid/{path}#L{start}-L{end}", (), ())


def run_cli(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([
        "python3", "scripts/build_source_index.py", "--source-root", str(source),
        "--snapshot-id", "qwen3-tts-022e286b",
        "--revision", "022e286b98fbec7e1e916cb940cdf532cd9f488e",
        "--output", str(output),
    ], cwd=ROOT, text=True, capture_output=True)


class SourceIndexTest(unittest.TestCase):
    def test_builds_files_symbols_and_config_keys_without_git(self):
        data = build_index(FIXTURE, SNAPSHOT)
        self.assertEqual(len(data["files"]), 5)
        qualnames = [row["qualname"] for row in data["symbols"]]
        self.assertTrue({"SampleConfig", "SampleConfig.__init__", "SampleConfig.describe", "build"}.issubset(qualnames))
        keys = {row["key"] for row in data["configs"]}
        self.assertTrue({"DEFAULT_RATE", "SampleConfig.model_type", "SampleConfig.width", "model.name", "training.precision"}.issubset(keys))
        self.assertNotIn("LOCAL_ONLY", keys)
        self.assertNotIn("SampleConfig.NOT_CONFIG", keys)
        symbol_ids = [row["id"] for row in data["symbols"]]
        self.assertEqual(len(symbol_ids), len(set(symbol_ids)))
        self.assertEqual(len([row for row in data["symbols"] if row["qualname"] == "DuplicateNames.value"]), 2)
        self.assertEqual(len([row for row in data["symbols"] if row["qualname"] == "DuplicateNames.overloaded"]), 2)
        self.assertTrue(all(row["id"] == f'{row["path"]}:{row["qualname"]}:{row["line"]}' for row in data["symbols"]))
        self.assertTrue(all((row["kind"] == "binary") == (row["line_count"] is None) for row in data["files"]))
        self.assertEqual(validate_source_index(data, {"fixture": SNAPSHOT}), [])

    def test_same_tree_produces_identical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "one.json", Path(tmp) / "two.json"
            data = build_index(FIXTURE, SNAPSHOT)
            write_canonical_json(data, first)
            write_canonical_json(build_index(FIXTURE, SNAPSHOT), second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_cli_requires_explicit_revision_and_rejects_mismatch(self):
        result = subprocess.run([
            "python3", "scripts/build_source_index.py", "--source-root", str(FIXTURE),
            "--snapshot-id", "qwen3-tts-022e286b", "--revision", "0" * 40,
            "--output", "/tmp/should-not-exist.json",
        ], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("revision does not match registry", result.stderr)

    def test_rejects_symlinks_before_hashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            (source / "safe.py").write_text("VALUE = 1\n")
            (source / "escape.py").symlink_to(FIXTURE / "pkg/sample.py")
            with self.assertRaisesRegex(ValueError, "symlink forbidden: escape.py"):
                build_index(source, SNAPSHOT)

    def test_rejects_source_root_symlink_and_output_inside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "real"
            real.mkdir()
            alias = Path(tmp) / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "source root symlink forbidden"):
                build_index(alias, SNAPSHOT)
            result = run_cli(alias, Path(tmp) / "outside.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("source root symlink forbidden", result.stderr)
            result = run_cli(real, real / "index.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("output must be outside source root", result.stderr)

    def test_extensionless_and_packaging_files_are_text_metadata(self):
        names = ["LICENSE", "Makefile", "Dockerfile", "MANIFEST.in", ".gitignore", "README"]
        self.assertEqual([file_kind(Path(name)) for name in names], ["text"] * len(names))
