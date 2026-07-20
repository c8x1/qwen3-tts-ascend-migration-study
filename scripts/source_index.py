from __future__ import annotations

import ast
import hashlib
import json
import re
import tomllib
from pathlib import Path

from scripts.phase2_contracts import Snapshot

PRUNED = {".git", "__pycache__", ".pytest_cache", "node_modules", "playwright-report", "test-results"}
KINDS = {".py": "python", ".json": "json", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml"}
TEXT_SUFFIXES = {".md", ".rst", ".txt", ".sh", ".css", ".js", ".html", ".c", ".h", ".in"}
TEXT_NAMES = {"LICENSE", "Makefile", "Dockerfile", "README", ".gitignore", ".gitattributes", ".gitmodules"}


def discover_files(source_root: Path) -> list[Path]:
    if source_root.is_symlink():
        raise ValueError("source root symlink forbidden")
    if not source_root.is_dir():
        raise ValueError(f"source root is not a directory: {source_root}")
    files = []
    for path in source_root.rglob("*"):
        relative = path.relative_to(source_root)
        if PRUNED.intersection(relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {relative.as_posix()}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(source_root).as_posix())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_kind(path: Path) -> str:
    if path.suffix.lower() in KINDS:
        return KINDS[path.suffix.lower()]
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
        return "text"
    return "binary"


def symbol_rows(path: Path, relative: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    rows = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            rows.append(_symbol(relative, node.name, node.name, "class", node))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    kind = "async_method" if isinstance(child, ast.AsyncFunctionDef) else "method"
                    rows.append(_symbol(relative, f"{node.name}.{child.name}", child.name, kind, child))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            rows.append(_symbol(relative, node.name, node.name, kind, node))
    return rows


def _symbol(path: str, qualname: str, name: str, kind: str, node: ast.AST) -> dict[str, object]:
    return {"id": f"{path}:{qualname}:{node.lineno}", "path": path, "qualname": qualname, "name": name, "kind": kind, "line": node.lineno, "end_line": node.end_lineno}


def config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return python_config_rows(path, relative)
    if suffix == ".json":
        return nested_config_rows(json.loads(path.read_text(encoding="utf-8")), relative, "json-key")
    if suffix == ".toml":
        return nested_config_rows(tomllib.loads(path.read_text(encoding="utf-8")), relative, "toml-key")
    if suffix in {".yaml", ".yml"}:
        return yaml_config_rows(path, relative)
    return []


def python_config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    visitor = ConfigVisitor(relative)
    visitor.visit(tree)
    return visitor.rows


class ConfigVisitor(ast.NodeVisitor):
    def __init__(self, relative: str):
        self.relative = relative
        self.owners: list[str] = []
        self.function_depth = 0
        self.rows: list[dict[str, object]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.owners.append(node.name)
        self.generic_visit(node)
        self.owners.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        self._record(node.targets, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record([node.target], node.lineno)
        self.generic_visit(node)

    def _record(self, targets: list[ast.expr], line: int) -> None:
        owner = ".".join(self.owners)
        for target in targets:
            name = None
            if isinstance(target, ast.Name) and self.function_depth == 0 and (target.id.isupper() or target.id in {"model_type", "sub_configs"}):
                name = target.id
            elif self.owners and self.function_depth == 1 and isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                name = target.attr
            if name is None:
                continue
            key = f"{owner}.{name}" if owner else name
            self.rows.append({"id": f"{self.relative}:{key}:{line}", "path": self.relative, "key": key, "owner": owner, "kind": "python-assignment", "line": line})


def nested_config_rows(data: object, relative: str, kind: str, prefix: str = "") -> list[dict[str, object]]:
    rows = []
    if isinstance(data, dict):
        for key in sorted(data):
            dotted = f"{prefix}.{key}" if prefix else str(key)
            rows.append({"id": f"{relative}:{dotted}:1", "path": relative, "key": dotted, "owner": prefix, "kind": kind, "line": 1})
            rows.extend(nested_config_rows(data[key], relative, kind, dotted))
    return rows


def yaml_config_rows(path: Path, relative: str) -> list[dict[str, object]]:
    rows, stack = [], []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = re.match(r"^( *)([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if not match or line.lstrip().startswith("#"):
            continue
        depth = len(match.group(1))
        stack = [(indent, key) for indent, key in stack if indent < depth]
        stack.append((depth, match.group(2)))
        dotted = ".".join(key for _, key in stack)
        rows.append({"id": f"{relative}:{dotted}:{line_number}", "path": relative, "key": dotted, "owner": ".".join(key for _, key in stack[:-1]), "kind": "yaml-key", "line": line_number})
    return rows


def build_index(source_root: Path, snapshot: Snapshot) -> dict[str, object]:
    files, symbols, configs = [], [], []
    for path in discover_files(source_root):
        relative = path.relative_to(source_root).as_posix()
        kind = file_kind(path)
        raw = path.read_bytes()
        line_count = None if kind == "binary" else len(raw.decode("utf-8", errors="replace").splitlines())
        files.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "kind": kind, "line_count": line_count})
        symbols.extend(symbol_rows(path, relative))
        configs.extend(config_rows(path, relative))
    payload = {
        "schema_version": 1,
        "snapshot": {key: getattr(snapshot, key) for key in ("snapshot_id", "project", "role", "revision", "acquisition_kind", "content_id")},
        "indexer_version": "1.0",
        "files": sorted(files, key=lambda row: row["path"]),
        "symbols": sorted(symbols, key=lambda row: row["id"]),
        "configs": sorted(configs, key=lambda row: row["id"]),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    payload["content_digest"] = hashlib.sha256(canonical).hexdigest()
    return payload


def write_canonical_json(data: object, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
