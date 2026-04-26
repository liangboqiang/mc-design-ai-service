from __future__ import annotations

from tool.stateful import StatefulToolbox


class AutonomyCapability(StatefulToolbox):
    toolbox_name = "autonomy"

    def executors(self):
        return {
            'autonomy.claim_next_task': self._exec_autonomy_claim_next_task,
        }

    def _exec_autonomy_claim_next_task(self, args: dict):
        return self.claim_next(args['owner'])

    def claim_next(self, owner: str) -> str:
        task_cap = self.capability("task")
        if task_cap is None:
            return "Task capability not enabled."
        unclaimed = task_cap.unclaimed_tasks()
        if not unclaimed:
            return "No unclaimed tasks."
        return task_cap.claim(int(unclaimed[0]["id"]), owner)

    def idle_tick(self) -> str:
        return self.claim_next(self.runtime.engine_id)
