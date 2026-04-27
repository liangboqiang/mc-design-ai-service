from __future__ import annotations

import difflib
import json
import os
import shutil
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".xml", ".csv", ".sql", ".sh", ".bat", ".ps1",
}


class FileToolbox:
    """Workspace-scoped file operations.

    All paths are relative to the kernel workspace root.  This toolbox provides
    deterministic file IO primitives and never accesses files outside the bound
    workspace.
    """

    toolbox_name = "files"
    tags = ("builtin", "workspace", "io")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "FileToolbox":
        return FileToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "files.stat": self._exec_stat,
            "files.list": self._exec_list,
            "files.list_dir": self._exec_list,       # compatibility alias for notes only
            "files.read_text": self._exec_read_text,
            "files.write_text": self._exec_write_text,
            "files.replace_text": self._exec_replace_text,
            "files.edit_text": self._exec_replace_text,  # compatibility alias for notes only
            "files.apply_patch": self._exec_apply_patch,
            "files.diff_text": self._exec_diff_text,
            "files.mkdir": self._exec_mkdir,
            "files.copy": self._exec_copy,
            "files.move": self._exec_move,
            "files.delete": self._exec_delete,
        }

    def _root(self) -> Path:
        if self.workspace_root is None:
            raise ValueError("FileToolbox workspace not bound yet.")
        return self.workspace_root.resolve()

    def _safe_path(self, raw: str) -> Path:
        path = (self._root() / str(raw or "").strip()).resolve()
        if not path.is_relative_to(self._root()):
            raise ValueError(f"Path escapes workspace: {raw}")
        return path

    def _rel(self, path: Path) -> str:
        return path.resolve().relative_to(self._root()).as_posix()

    def _exec_stat(self, args: dict[str, Any]):
        path = self._safe_path(args.get("path", "."))
        if not path.exists():
            return json.dumps({"exists": False, "path": args.get("path", "")}, ensure_ascii=False)
        stat = path.stat()
        return json.dumps({
            "exists": True,
            "path": self._rel(path),
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "modified_at": int(stat.st_mtime),
        }, ensure_ascii=False, indent=2)

    def _exec_list(self, args: dict[str, Any]):
        path = self._safe_path(args.get("path", "."))
        recursive = bool(args.get("recursive", False))
        limit = max(1, min(int(args.get("limit", 200) or 200), 1000))
        if not path.exists():
            raise FileNotFoundError(str(args.get("path", ".")))
        iterator = path.rglob("*") if recursive and path.is_dir() else path.iterdir() if path.is_dir() else [path]
        rows = []
        for item in sorted(iterator, key=lambda p: p.as_posix()):
            if len(rows) >= limit:
                break
            try:
                rows.append({
                    "path": self._rel(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
            except OSError:
                continue
        return json.dumps({"root": self._rel(path), "items": rows, "truncated": len(rows) >= limit}, ensure_ascii=False, indent=2)

    def _exec_read_text(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        max_chars = max(1, min(int(args.get("max_chars", 20000) or 20000), 200000))
        start_line = max(1, int(args.get("start_line", 1) or 1))
        end_line = int(args.get("end_line", 0) or 0)
        text = path.read_text(encoding=args.get("encoding") or "utf-8", errors="replace")
        if start_line > 1 or end_line > 0:
            lines = text.splitlines()
            selected = lines[start_line - 1 : end_line or None]
            text = "\n".join(selected)
        return text[:max_chars]

    def _exec_write_text(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        content = str(args.get("content", ""))
        overwrite = bool(args.get("overwrite", True))
        if path.exists() and not overwrite:
            raise FileExistsError(self._rel(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=args.get("encoding") or "utf-8")
        return json.dumps({"status": "written", "path": self._rel(path), "chars": len(content)}, ensure_ascii=False)

    def _exec_replace_text(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        old_text = str(args.get("old_text", ""))
        new_text = str(args.get("new_text", ""))
        if not old_text:
            raise ValueError("old_text cannot be empty")
        text = path.read_text(encoding="utf-8", errors="replace")
        count = int(args.get("count", 1) or 1)
        if old_text not in text:
            raise ValueError(f"old_text not found in {self._rel(path)}")
        updated = text.replace(old_text, new_text, count)
        path.write_text(updated, encoding="utf-8")
        return json.dumps({"status": "replaced", "path": self._rel(path), "replacements": min(count, text.count(old_text))}, ensure_ascii=False)

    def _exec_apply_patch(self, args: dict[str, Any]):
        # Lightweight single-file patch: accepts either {old_text,new_text} or a list of replacements.
        path = self._safe_path(args["path"])
        replacements = args.get("replacements") or [{"old_text": args.get("old_text", ""), "new_text": args.get("new_text", "")}]
        text = path.read_text(encoding="utf-8", errors="replace")
        applied = 0
        for row in replacements:
            old_text = str(row.get("old_text", ""))
            new_text = str(row.get("new_text", ""))
            if not old_text or old_text not in text:
                raise ValueError(f"patch fragment not found in {self._rel(path)}")
            text = text.replace(old_text, new_text, int(row.get("count", 1) or 1))
            applied += 1
        path.write_text(text, encoding="utf-8")
        return json.dumps({"status": "patched", "path": self._rel(path), "fragments": applied}, ensure_ascii=False)

    def _exec_diff_text(self, args: dict[str, Any]):
        old_path = self._safe_path(args["old_path"])
        new_path = self._safe_path(args["new_path"])
        old_lines = old_path.read_text(encoding="utf-8", errors="replace").splitlines()
        new_lines = new_path.read_text(encoding="utf-8", errors="replace").splitlines()
        diff = difflib.unified_diff(old_lines, new_lines, fromfile=self._rel(old_path), tofile=self._rel(new_path), lineterm="")
        return "\n".join(diff)

    def _exec_mkdir(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        path.mkdir(parents=True, exist_ok=True)
        return json.dumps({"status": "created", "path": self._rel(path)}, ensure_ascii=False)

    def _exec_copy(self, args: dict[str, Any]):
        source = self._safe_path(args["source"])
        target = self._safe_path(args["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if target.exists():
                raise FileExistsError(self._rel(target))
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        return json.dumps({"status": "copied", "source": self._rel(source), "target": self._rel(target)}, ensure_ascii=False)

    def _exec_move(self, args: dict[str, Any]):
        source = self._safe_path(args["source"])
        target = self._safe_path(args["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        return json.dumps({"status": "moved", "source": str(args["source"]), "target": self._rel(target)}, ensure_ascii=False)

    def _exec_delete(self, args: dict[str, Any]):
        path = self._safe_path(args["path"])
        if path == self._root():
            raise ValueError("Cannot delete workspace root")
        recursive = bool(args.get("recursive", False))
        if path.is_dir():
            if not recursive:
                raise ValueError("Deleting a directory requires recursive=true")
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        return json.dumps({"status": "deleted", "path": str(args["path"])}, ensure_ascii=False)
