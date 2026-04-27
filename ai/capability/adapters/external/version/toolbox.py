from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workbench.version_service import NoteVersionService


class VersionToolbox:
    toolbox_name = "version"
    tags = ("builtin", "governance", "version")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.project_root: Path | None = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self.project_root = Path(getattr(runtime, "project_root", Path.cwd())).resolve()

    def spawn(self, workspace_root: Path) -> "VersionToolbox":
        return VersionToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "version.status": self._exec_status,
            "version.commit": self._exec_commit,
            "version.history": self._exec_history,
            "version.diff": self._exec_diff,
            "version.restore": self._exec_restore,
            "version.release": self._exec_release,
            "version.rollback": self._exec_rollback,
        }

    def _svc(self) -> NoteVersionService:
        if self.project_root is None:
            raise ValueError("VersionToolbox runtime not bound")
        return NoteVersionService(self.project_root)

    def _exec_status(self, args: dict[str, Any]):
        return json.dumps(self._svc().status(), ensure_ascii=False, indent=2)

    def _exec_commit(self, args: dict[str, Any]):
        return json.dumps(self._svc().commit_notes(message=str(args.get("message") or "tool commit"), author=str(args.get("author") or "agent"), scope=str(args.get("scope") or "all")), ensure_ascii=False, indent=2)

    def _exec_history(self, args: dict[str, Any]):
        if args.get("note_id") or args.get("note_path"):
            data = self._svc().note_history(note_path=str(args.get("note_path") or ""), note_id=str(args.get("note_id") or ""), limit=int(args.get("limit", 50) or 50))
        else:
            data = self._svc().list_commits(limit=int(args.get("limit", 50) or 50))
        return json.dumps({"history": data}, ensure_ascii=False, indent=2)

    def _exec_diff(self, args: dict[str, Any]):
        return json.dumps(self._svc().diff_note_versions(note_path=str(args.get("note_path") or ""), note_id=str(args.get("note_id") or ""), from_commit=str(args.get("from_commit") or ""), to_commit=str(args.get("to_commit") or "WORKTREE")), ensure_ascii=False, indent=2)

    def _exec_restore(self, args: dict[str, Any]):
        return json.dumps(self._svc().restore_note_version(note_path=str(args.get("note_path") or ""), note_id=str(args.get("note_id") or ""), commit_id=str(args["commit_id"]), message=str(args.get("message") or "restore by tool")), ensure_ascii=False, indent=2)

    def _exec_release(self, args: dict[str, Any]):
        return json.dumps(self._svc().create_release(name=str(args.get("name") or ""), message=str(args.get("message") or "")), ensure_ascii=False, indent=2)

    def _exec_rollback(self, args: dict[str, Any]):
        return json.dumps(self._svc().rollback_release(release_id=str(args["release_id"]), message=str(args.get("message") or "rollback by tool")), ensure_ascii=False, indent=2)
