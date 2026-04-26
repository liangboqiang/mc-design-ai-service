from __future__ import annotations

from pathlib import Path
from .ops import EngineOps


class EngineToolbox:
    toolbox_name = "engine"
    discoverable = False
    tags = ("engine", "runtime")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "EngineToolbox":
        return EngineToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            'engine.inspect_skill': self._exec_engine_inspect_skill,
            'engine.inspect_tool': self._exec_engine_inspect_tool,
            'engine.enter_skill': self._exec_engine_enter_skill,
            'engine.list_child_skills': self._exec_engine_list_child_skills,
        }

    def _exec_engine_inspect_skill(self, args: dict):
        return self._ops().inspect_skill(args['skill'])

    def _exec_engine_inspect_tool(self, args: dict):
        return self._ops().inspect_tool(args['tool'])

    def _exec_engine_enter_skill(self, args: dict):
        return self._ops().enter_skill(args['skill'])

    def _exec_engine_list_child_skills(self, args: dict):
        return self._ops().list_child_skills()

    def _ops(self) -> EngineOps:
        if self.runtime is None:
            raise RuntimeError("EngineToolbox runtime not bound yet.")
        return EngineOps(
            registry=self.runtime.registry,
            skill_state=self.runtime.skill_state,
            context=self.runtime.context,
            events=self.runtime.events,
            tool_registry=self.runtime.runtime_state.tool_registry,
        )
