from __future__ import annotations

import base64
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from workbench.file_extractors import extract_text
from workspace_paths import data_root, workspace_root


class WorkspaceFileService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.base = data_root(self.project_root) / "workbench"
        self.team_root = self.base / "team"
        self.user_root = self.base / "user"
        for path in (self.team_root, self.user_root):
            path.mkdir(parents=True, exist_ok=True)

    def roots(self) -> dict[str, Any]:
        return {
            "team": self._rel(self.team_root),
            "user": self._rel(self.user_root),
            "system_notes": self._rel(data_root(self.project_root) / "notes"),
            "indexes": self._rel(data_root(self.project_root) / "indexes"),
        }

    def list_files(self, scope: str = "team", path: str = "", recursive: bool = False) -> dict[str, Any]:
        root = self._scope_root(scope)
        base = self._safe_path(root, path, allow_missing=True)
        if not base.exists():
            base.mkdir(parents=True, exist_ok=True)
        rows = []
        iterator = base.rglob("*") if recursive else base.iterdir()
        for item in sorted(iterator, key=lambda p: (p.is_file(), p.name.lower())):
            if item.name.startswith("."):
                continue
            rel = item.relative_to(root).as_posix()
            stat = item.stat()
            rows.append(
                {
                    "name": item.name,
                    "path": rel,
                    "kind": "folder" if item.is_dir() else "file",
                    "size": 0 if item.is_dir() else stat.st_size,
                    "modified_at": _ts(stat.st_mtime),
                    "suffix": item.suffix.lower(),
                }
            )
        return {"scope": scope, "path": path, "root": self._rel(root), "items": rows}

    def read_file(self, scope: str = "team", path: str = "") -> dict[str, Any]:
        root = self._scope_root(scope)
        target = self._safe_path(root, path)
        if target.is_dir():
            return self.list_files(scope=scope, path=path)
        text = _read_text(target)
        return {
            "scope": scope,
            "path": target.relative_to(root).as_posix(),
            "name": target.name,
            "size": target.stat().st_size,
            "modified_at": _ts(target.stat().st_mtime),
            "content": text,
            "extract": extract_text(target, max_chars=80_000),
        }

    def write_file(self, scope: str = "team", path: str = "", content: str = "", create_dirs: bool = True) -> dict[str, Any]:
        if not str(path or "").strip():
            raise ValueError("缺少 path")
        root = self._scope_root(scope)
        target = self._safe_path(root, path, allow_missing=True)
        if create_dirs:
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content or ""), encoding="utf-8")
        return {"status": "written", "scope": scope, "path": target.relative_to(root).as_posix(), "size": target.stat().st_size}

    def upload_files(self, scope: str = "team", path: str = "", files: list[dict] | None = None) -> dict[str, Any]:
        root = self._scope_root(scope)
        base = self._safe_path(root, path, allow_missing=True)
        base.mkdir(parents=True, exist_ok=True)
        saved = []
        for item in files or []:
            name = str(item.get("relative_path") or item.get("path") or item.get("name") or "").replace("\\", "/").strip("/")
            if not name:
                continue
            target = self._safe_path(base, name, allow_missing=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.get("encoding") == "base64":
                target.write_bytes(base64.b64decode(str(item.get("content") or "")))
            else:
                target.write_text(str(item.get("content") or ""), encoding="utf-8")
            saved.append({"path": target.relative_to(root).as_posix(), "size": target.stat().st_size})
        return {"status": "uploaded", "scope": scope, "base_path": path, "count": len(saved), "files": saved}

    def make_dir(self, scope: str = "team", path: str = "") -> dict[str, Any]:
        root = self._scope_root(scope)
        target = self._safe_path(root, path, allow_missing=True)
        target.mkdir(parents=True, exist_ok=True)
        return {"status": "created", "scope": scope, "path": target.relative_to(root).as_posix()}

    def delete_file(self, scope: str = "team", path: str = "") -> dict[str, Any]:
        root = self._scope_root(scope)
        target = self._safe_path(root, path)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return {"status": "deleted", "scope": scope, "path": str(path)}

    def move_file(self, scope: str = "team", source: str = "", target: str = "") -> dict[str, Any]:
        root = self._scope_root(scope)
        src = self._safe_path(root, source)
        dst = self._safe_path(root, target, allow_missing=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"status": "moved", "scope": scope, "source": source, "target": dst.relative_to(root).as_posix()}

    def extract_file(self, scope: str = "team", path: str = "") -> dict[str, Any]:
        root = self._scope_root(scope)
        target = self._safe_path(root, path)
        if target.is_dir():
            rows = []
            for file in sorted(p for p in target.rglob("*") if p.is_file()):
                rows.append(extract_text(file, max_chars=30_000))
            return {"scope": scope, "path": path, "items": rows, "count": len(rows)}
        return {"scope": scope, "path": path, "item": extract_text(target)}

    def create_user_session(self, user_id: str = "default", session_id: str = "default") -> dict[str, Any]:
        root = self._user_session_root(user_id, session_id)
        for name in ("attachments", "generated", "handoff", "temp_notes"):
            (root / name).mkdir(parents=True, exist_ok=True)
        manifest = root / "session_manifest.json"
        if not manifest.exists():
            manifest.write_text(json.dumps({"user_id": user_id, "session_id": session_id, "created_at": _now()}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "ready", "root": self._rel(root), "user_id": user_id, "session_id": session_id}

    def submit_user_file_to_team(self, user_id: str = "default", session_id: str = "default", path: str = "", target: str = "incoming") -> dict[str, Any]:
        session_root = self._user_session_root(user_id, session_id)
        source = self._safe_path(session_root, path)
        team_target = self._safe_path(self.team_root, target, allow_missing=True) / source.name
        team_target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if team_target.exists():
                shutil.rmtree(team_target)
            shutil.copytree(source, team_target)
        else:
            shutil.copy2(source, team_target)
        return {"status": "submitted", "source": source.relative_to(session_root).as_posix(), "target": team_target.relative_to(self.team_root).as_posix()}

    def _scope_root(self, scope: str) -> Path:
        normalized = str(scope or "team").lower()
        if normalized == "team":
            return self.team_root
        if normalized == "user":
            return self.user_root
        if normalized == "notes":
            return data_root(self.project_root) / "notes"
        raise ValueError(f"未知 workspace scope：{scope}")

    def _user_session_root(self, user_id: str, session_id: str) -> Path:
        safe_user = _safe_segment(user_id or "default")
        safe_session = _safe_segment(session_id or "default")
        root = self.user_root / safe_user / safe_session
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _safe_path(self, root: Path, rel: str, allow_missing: bool = False) -> Path:
        root = Path(root).resolve()
        target = (root / str(rel or "").strip().lstrip("/\\")).resolve()
        if root not in [target, *target.parents]:
            raise ValueError("路径越界")
        if not allow_missing and not target.exists():
            raise FileNotFoundError(target.relative_to(root).as_posix())
        return target

    def _rel(self, path: Path) -> str:
        try:
            return Path(path).resolve().relative_to(workspace_root(self.project_root)).as_posix()
        except Exception:  # noqa: BLE001
            return Path(path).as_posix()


def _safe_segment(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(value or ""))[:80] or "default"


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ts(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))
