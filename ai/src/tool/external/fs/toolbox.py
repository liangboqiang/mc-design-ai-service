from __future__ import annotations

import difflib
from pathlib import Path


class FileToolbox:
    toolbox_name = "files"
    tags = ("builtin", "workspace", "io")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "FileToolbox":
        return FileToolbox(workspace_root=workspace_root)

    def _safe_path(self, raw: str) -> Path:
        if self.workspace_root is None:
            raise ValueError("FileToolbox workspace not bound yet.")
        path = (self.workspace_root / raw).resolve()
        if not path.is_relative_to(self.workspace_root):
            raise ValueError(f"Path escapes workspace: {raw}")
        return path

    def executors(self):
        return {
            'files.read_text': self._exec_files_read_text,
            'files.write_text': self._exec_files_write_text,
            'files.edit_text': self._exec_files_edit_text,
            'files.list_dir': self._exec_files_list_dir,
            'files.diff_text': self._exec_files_diff_text,
        }

    def _exec_files_read_text(self, args: dict):
        return self._safe_path(args['path']).read_text(encoding='utf-8')

    def _exec_files_write_text(self, args: dict):
        return self._write(args['path'], args['content'])

    def _exec_files_edit_text(self, args: dict):
        return self._edit(args['path'], args['old_text'], args['new_text'])

    def _exec_files_list_dir(self, args: dict):
        return self._list_dir(args['path'])

    def _exec_files_diff_text(self, args: dict):
        return self._diff(args['old_path'], args['new_path'])

    def _write(self, path: str, content: str) -> str:
        target = self._safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"

    def _edit(self, path: str, old_text: str, new_text: str) -> str:
        target = self._safe_path(path)
        content = target.read_text(encoding="utf-8")
        if old_text not in content:
            raise ValueError(f"old_text not found in {path}")
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {path}"

    def _list_dir(self, path: str) -> str:
        target = self._safe_path(path)
        if not target.exists():
            raise FileNotFoundError(path)
        return "\n".join(item.name + ("/" if item.is_dir() else "") for item in sorted(target.iterdir()))

    def _diff(self, old_path: str, new_path: str) -> str:
        old_lines = self._safe_path(old_path).read_text(encoding="utf-8").splitlines()
        new_lines = self._safe_path(new_path).read_text(encoding="utf-8").splitlines()
        return "\n".join(
            difflib.unified_diff(old_lines, new_lines, fromfile=old_path, tofile=new_path, lineterm="")
        )
