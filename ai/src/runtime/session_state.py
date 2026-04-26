from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.types import EngineSettings
from storage.history_store import HistoryStore
from storage.inbox_store import InboxStore
from storage.json_store import JsonStore
from storage.runtime_paths import ensure_runtime_paths
from storage.task_store import TaskStore
from storage.transcript_store import TranscriptStore
from storage.workspace_store import WorkspaceStore


class SessionState:
    def __init__(self, settings: EngineSettings, storage_base: Path):
        self.settings = settings
        self.paths = ensure_runtime_paths(
            storage_base,
            settings.user_id,
            settings.conversation_id,
            settings.task_id,
        )
        self.workspace_root = (self.paths.root / "workspace_root").resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.history = HistoryStore(self.paths.history_dir)
        self.tasks = TaskStore(self.paths.state_dir)
        self.workspaces = WorkspaceStore(self.paths.workspace_dir)
        self.inbox = InboxStore(self.paths.inbox_dir)
        self.transcripts = TranscriptStore(self.paths.logs_dir)
        self.attachments_root = self.paths.attachments_dir.resolve()
        self.attachments_root.mkdir(parents=True, exist_ok=True)

    def state_store(self, name: str) -> JsonStore:
        target = (self.paths.state_dir / name).resolve()
        if not target.is_relative_to(self.paths.state_dir.resolve()):
            raise ValueError(f"State path escapes state dir: {name}")
        return JsonStore(target)

    def read_state_json(self, name: str, default: Any):
        return self.state_store(name).read(default)

    def write_state_json(self, name: str, payload: Any) -> None:
        self.state_store(name).write(payload)
