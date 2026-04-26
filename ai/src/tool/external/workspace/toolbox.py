from __future__ import annotations

import json
import subprocess

from tool.stateful import StatefulToolbox


class WorkspaceCapability(StatefulToolbox):
    toolbox_name = "workspace"

    def executors(self):
        return {
            'workspace.create': self._exec_workspace_create,
            'workspace.list': self._exec_workspace_list,
            'workspace.run': self._exec_workspace_run,
            'workspace.keep': self._exec_workspace_keep,
            'workspace.remove': self._exec_workspace_remove,
        }

    def _exec_workspace_create(self, args: dict):
        return self.create(args['name'], args.get('task_id'))

    def _exec_workspace_list(self, args: dict):
        return json.dumps({'workspaces': self.runtime.session.workspaces.list_all()}, ensure_ascii=False, indent=2)

    def _exec_workspace_run(self, args: dict):
        return self.run(args['name'], args['command'])

    def _exec_workspace_keep(self, args: dict):
        return self.keep(args['name'])

    def _exec_workspace_remove(self, args: dict):
        return self.remove(args['name'], bool(args.get('complete_task', False)))

    def create(self, name: str, task_id: int | None) -> str:
        row = self.runtime.session.workspaces.create(name, task_id)
        task_cap = self.capability("task")
        if task_id and task_cap:
            task_cap.update(
                task_id,
                status="in_progress",
                owner=self.runtime.engine_id,
                add_blocked_by=[],
                remove_blocked_by=[],
            )
        self.runtime.events.emit("workspace.created", workspace=row)
        return json.dumps(row, ensure_ascii=False, indent=2)

    def run(self, name: str, command: str) -> str:
        row = self.runtime.session.workspaces.get(name)
        completed = subprocess.run(command, shell=True, cwd=row["path"], capture_output=True, text=True, timeout=300)
        output = (completed.stdout + completed.stderr).strip()
        self.runtime.events.emit("workspace.command_ran", workspace=name, command=command)
        return output[:50000] if output else "(no output)"

    def keep(self, name: str) -> str:
        row = self.runtime.session.workspaces.keep(name)
        self.runtime.events.emit("workspace.kept", workspace=row)
        return f"Workspace {name} kept"

    def remove(self, name: str, complete_task: bool) -> str:
        row = self.runtime.session.workspaces.remove(name)
        task_cap = self.capability("task")
        if complete_task and row.get("task_id") and task_cap:
            task_cap.update(
                int(row["task_id"]),
                status="completed",
                owner=self.runtime.engine_id,
                add_blocked_by=[],
                remove_blocked_by=[],
            )
        self.runtime.events.emit("workspace.removed", workspace=row, complete_task=complete_task)
        return f"Workspace {name} removed"
