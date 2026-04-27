from __future__ import annotations

import ast
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".runtime_data"}
TEXT_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".md", ".json", ".yaml", ".yml", ".toml", ".sql", ".txt"}


class CodeToolbox:
    toolbox_name = "code"
    tags = ("builtin", "code", "search")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "CodeToolbox":
        return CodeToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "code.glob": self._exec_glob,
            "code.grep": self._exec_grep,
            "code.read_window": self._exec_read_window,
            "code.symbols": self._exec_symbols,
            "code.repo_map": self._exec_repo_map,
        }

    def _root(self) -> Path:
        if self.workspace_root is None:
            raise ValueError("CodeToolbox workspace not bound yet.")
        return self.workspace_root.resolve()

    def _safe_path(self, raw: str = ".") -> Path:
        path = (self._root() / (raw or ".")).resolve()
        if not path.is_relative_to(self._root()):
            raise ValueError(f"Path escapes workspace: {raw}")
        return path

    def _walk(self, root: Path):
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            if path.is_file():
                yield path

    def _rel(self, path: Path) -> str:
        return path.resolve().relative_to(self._root()).as_posix()

    def _exec_glob(self, args: dict[str, Any]):
        pattern = str(args.get("pattern") or "**/*")
        root = self._safe_path(args.get("path", "."))
        limit = max(1, min(int(args.get("limit", 200) or 200), 1000))
        rows = []
        for path in self._walk(root):
            rel = self._rel(path)
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern):
                rows.append(rel)
                if len(rows) >= limit:
                    break
        return json.dumps({"matches": rows, "truncated": len(rows) >= limit}, ensure_ascii=False, indent=2)

    def _exec_grep(self, args: dict[str, Any]):
        pattern = str(args["pattern"])
        file_glob = str(args.get("file_glob") or "**/*")
        root = self._safe_path(args.get("path", "."))
        limit = max(1, min(int(args.get("limit", 100) or 100), 500))
        flags = 0 if args.get("case_sensitive") else re.IGNORECASE
        rx = re.compile(pattern, flags)
        rows = []
        for path in self._walk(root):
            rel = self._rel(path)
            if path.suffix.lower() not in TEXT_EXTS or not (fnmatch.fnmatch(rel, file_glob) or fnmatch.fnmatch(path.name, file_glob)):
                continue
            try:
                for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    if rx.search(line):
                        rows.append({"path": rel, "line": lineno, "text": line[:300]})
                        if len(rows) >= limit:
                            return json.dumps({"matches": rows, "truncated": True}, ensure_ascii=False, indent=2)
            except OSError:
                continue
        return json.dumps({"matches": rows, "truncated": False}, ensure_ascii=False, indent=2)

    def _exec_read_window(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        start = max(1, int(args.get("start_line", 1) or 1))
        window = max(1, min(int(args.get("window", 120) or 120), 500))
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = []
        for idx in range(start - 1, min(len(lines), start - 1 + window)):
            selected.append(f"{idx + 1:>5}: {lines[idx]}")
        return "\n".join(selected)

    def _exec_symbols(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        rel = self._rel(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        rows = []
        if path.suffix == ".py":
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        rows.append({"kind": node.__class__.__name__, "name": node.name, "line": getattr(node, "lineno", 0)})
            except SyntaxError as exc:
                return json.dumps({"path": rel, "error": str(exc), "symbols": []}, ensure_ascii=False, indent=2)
        else:
            rx = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)", re.MULTILINE)
            rows = [{"kind": "symbol", "name": m.group(1), "line": text[:m.start()].count("\n") + 1} for m in rx.finditer(text)]
        return json.dumps({"path": rel, "symbols": rows[:300]}, ensure_ascii=False, indent=2)

    def _exec_repo_map(self, args: dict[str, Any]):
        root = self._safe_path(args.get("path", "."))
        limit_files = max(1, min(int(args.get("limit_files", 80) or 80), 300))
        rows = []
        for path in self._walk(root):
            if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx"}:
                continue
            symbols = json.loads(self._exec_symbols({"path": self._rel(path)})).get("symbols", [])[:20]
            rows.append({"path": self._rel(path), "symbols": symbols})
            if len(rows) >= limit_files:
                break
        return json.dumps({"root": self._rel(root), "files": rows}, ensure_ascii=False, indent=2)
