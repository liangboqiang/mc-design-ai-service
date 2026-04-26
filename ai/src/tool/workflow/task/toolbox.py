from __future__ import annotations

import json

from tool.stateful import StatefulToolbox


class TaskCapability(StatefulToolbox):
    toolbox_name = "task"

    def executors(self):
        return {
            'task.create': self._exec_task_create,
            'task.update': self._exec_task_update,
            'task.list': self._exec_task_list,
            'task.get': self._exec_task_get,
            'task.claim': self._exec_task_claim,
        }

    def _exec_task_create(self, args: dict):
        return self.create(args['subject'], args.get('description', ''), args.get('blocked_by') or [])

    def _exec_task_update(self, args: dict):
        return self.update(args['task_id'], args.get('status'), args.get('owner'), args.get('add_blocked_by') or [], args.get('remove_blocked_by') or [])

    def _exec_task_list(self, args: dict):
        return self.list_all()

    def _exec_task_get(self, args: dict):
        return json.dumps(self.runtime.session.tasks.get(args['task_id']), ensure_ascii=False, indent=2)

    def _exec_task_claim(self, args: dict):
        return self.claim(args['task_id'], args['owner'])

    def create(self, subject: str, description: str, blocked_by: list[int]) -> str:
        payload = self.runtime.session.tasks.create(subject, description, blocked_by)
        if blocked_by:
            self.runtime.events.emit("task.blocked", task_id=payload["id"], blocked_by=blocked_by)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def update(self, task_id: int, status: str | None, owner: str | None, add_blocked_by: list[int], remove_blocked_by: list[int]) -> str:
        payload = self.runtime.session.tasks.update(
            task_id,
            status=status,
            owner=owner,
            add_blocked_by=add_blocked_by,
            remove_blocked_by=remove_blocked_by,
        )
        if payload.get("blocked_by"):
            self.runtime.events.emit("task.blocked", task_id=task_id, blocked_by=payload["blocked_by"])
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def claim(self, task_id: int, owner: str) -> str:
        payload = self.runtime.session.tasks.claim(task_id, owner)
        self.runtime.events.emit("task.claimed", task_id=task_id, owner=owner)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def list_all(self) -> str:
        return json.dumps(self.runtime.session.tasks.list_all(), ensure_ascii=False, indent=2)

    def unclaimed_tasks(self) -> list[dict]:
        return self.runtime.session.tasks.unclaimed()

    def state_fragments(self) -> list[str]:
        rows = self.runtime.session.tasks.list_all()
        if not rows:
            return ["tasks: (none)"]
        summary = "\n".join(
            f"- #{row['id']} {row['subject']} | {row['status']} | owner={row['owner'] or '-'} | blocked_by={row.get('blocked_by', [])}"
            for row in rows[:10]
        )
        return [f"tasks:\n{summary}"]
