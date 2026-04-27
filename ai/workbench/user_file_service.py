from __future__ import annotations

import shutil
import time
from pathlib import Path


class UserFileEvidenceService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def user_file_tree(self, relative_path: str = "") -> dict:
        root = self._user_files_root()
        folder = self._safe_user_path(relative_path)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        if not folder.is_dir():
            folder = folder.parent
        rows = []
        for item in sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if item.name.startswith("."):
                continue
            rows.append(
                {
                    "name": item.name,
                    "relative_path": item.relative_to(root).as_posix(),
                    "type": "folder" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.stat().st_mtime)),
                }
            )
        return {"root": str(root), "relative_path": folder.relative_to(root).as_posix() if folder != root else "", "items": rows}

    def user_file_read(self, relative_path: str) -> dict:
        path = self._safe_user_path(relative_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"用户文件不存在：{relative_path}")
        if path.stat().st_size > 1024 * 1024:
            return {"relative_path": path.relative_to(self._user_files_root()).as_posix(), "content": "", "binary_or_large": True, "message": "文件超过 1MB，仅显示元数据。"}
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="replace")
        return {"relative_path": path.relative_to(self._user_files_root()).as_posix(), "content": content, "size": path.stat().st_size}

    def user_file_write(self, relative_path: str, content: str = "") -> dict:
        path = self._safe_user_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content or ""), encoding="utf-8")
        return {"relative_path": path.relative_to(self._user_files_root()).as_posix(), "status": "saved", "size": path.stat().st_size}

    def user_file_mkdir(self, relative_path: str) -> dict:
        path = self._safe_user_path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return {"relative_path": path.relative_to(self._user_files_root()).as_posix(), "status": "created"}

    def user_file_delete(self, relative_path: str) -> dict:
        path = self._safe_user_path(relative_path)
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        return {"relative_path": str(relative_path or ""), "status": "deleted"}

    def user_center_summary(self, root_path: str = "") -> dict:
        root = Path(root_path).resolve() if root_path else self.project_root
        allowed = self.project_root in [root, *root.parents] or root in [self.project_root, *self.project_root.parents]
        return {"root_path": str(root), "inside_project": allowed}

    def _user_files_root(self) -> Path:
        root = self.project_root / "user_files"
        root.mkdir(parents=True, exist_ok=True)
        return root.resolve()

    def _safe_user_path(self, relative_path: str = "") -> Path:
        root = self._user_files_root()
        rel = str(relative_path or "").strip().lstrip("/\\")
        target = (root / rel).resolve()
        if root not in [target, *target.parents]:
            raise ValueError("用户文件路径越界。")
        return target
