from __future__ import annotations

from pathlib import Path

from .json_store import JsonStore


class TaskStore:
    def __init__(self, state_dir: Path):
        self.tasks_dir = state_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _task_path(self, task_id: int) -> Path:
        return self.tasks_dir / f"task_{task_id}.json"

    def _store(self, task_id: int) -> JsonStore:
        return JsonStore(self._task_path(task_id))

    def next_id(self) -> int:
        ids = [int(path.stem.split("_")[-1]) for path in self.tasks_dir.glob("task_*.json")]
        return (max(ids) if ids else 0) + 1

    def create(self, subject: str, description: str = "", blocked_by: list[int] | None = None) -> dict:
        payload = {
            "id": self.next_id(),
            "subject": subject,
            "description": description,
            "status": "pending",
            "owner": "",
            "blocked_by": blocked_by or [],
        }
        self._store(int(payload["id"])).write(payload)
        return payload

    def get(self, task_id: int) -> dict:
        payload = self._store(task_id).read(None)
        if payload is None:
            raise FileNotFoundError(f"Unknown task {task_id}")
        return payload

    def list_all(self) -> list[dict]:
        return [self.get(int(path.stem.split("_")[-1])) for path in sorted(self.tasks_dir.glob("task_*.json"))]

    def update(
        self,
        task_id: int,
        *,
        status: str | None = None,
        owner: str | None = None,
        add_blocked_by: list[int] | None = None,
        remove_blocked_by: list[int] | None = None,
    ) -> dict:
        payload = self.get(task_id)
        if status:
            payload["status"] = status
        if owner is not None:
            payload["owner"] = owner
        if add_blocked_by:
            payload["blocked_by"] = sorted(set(payload.get("blocked_by", []) + add_blocked_by))
        if remove_blocked_by:
            payload["blocked_by"] = [item for item in payload.get("blocked_by", []) if item not in remove_blocked_by]
        self._store(task_id).write(payload)
        if status == "completed":
            self.clear_dependency(task_id)
        return payload

    def claim(self, task_id: int, owner: str) -> dict:
        payload = self.get(task_id)
        if payload.get("owner"):
            raise ValueError(f"Task {task_id} already owned by {payload['owner']}")
        if payload.get("blocked_by"):
            raise ValueError(f"Task {task_id} is blocked by {payload['blocked_by']}")
        payload["owner"] = owner
        payload["status"] = "in_progress"
        self._store(task_id).write(payload)
        return payload

    def clear_dependency(self, completed_id: int) -> None:
        for row in self.list_all():
            blocked_by = row.get("blocked_by", [])
            if completed_id in blocked_by:
                row["blocked_by"] = [item for item in blocked_by if item != completed_id]
                self._store(int(row["id"])).write(row)

    def unclaimed(self) -> list[dict]:
        return [
            row
            for row in self.list_all()
            if row.get("status") == "pending" and not row.get("owner") and not row.get("blocked_by")
        ]
