from __future__ import annotations

from pathlib import Path

from kernel.state import RuntimePaths


def ensure_runtime_paths(base_dir: Path, user_id: str, conversation_id: str, task_id: str) -> RuntimePaths:
    root = base_dir / user_id / conversation_id / task_id
    history_dir = root / "history"
    state_dir = root / "state"
    workspace_dir = root / "workspaces"
    inbox_dir = root / "inbox"
    logs_dir = root / "logs"
    attachments_dir = root / "attachments"
    for path in (history_dir, state_dir, workspace_dir, inbox_dir, logs_dir, attachments_dir):
        path.mkdir(parents=True, exist_ok=True)
    return RuntimePaths(root, history_dir, state_dir, workspace_dir, inbox_dir, logs_dir, attachments_dir)
