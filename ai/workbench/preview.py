from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from capability import CapabilityRegistry, CapabilitySurfaceResolver
from kernel.policy import KernelPolicy
from kernel.prompt import PromptAssembler
from memory import MemoryService


class RuntimePreviewService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.memory = MemoryService(self.project_root)
        self.capability_registry = CapabilityRegistry.create(self.project_root, memory=self.memory)
        self.surface = CapabilitySurfaceResolver(self.capability_registry)
        self.prompt = PromptAssembler()

    def preview_view(self, task: str = "") -> dict:
        view = self.memory.orient(task)
        return asdict(view)

    def preview_runtime(self, task: str = "", tool_permission_level: int = 1) -> dict:
        task = str(task or "").strip()
        if not task:
            raise ValueError("缺少必要参数：task")
        policy = KernelPolicy(tool_permission_level=int(tool_permission_level or 1))
        memory_view = self.memory.orient(task)
        capability_view = self.surface.resolve(
            observation=task,
            memory_view=memory_view,
            policy={
                "tool_permission_level": policy.tool_permission_level,
                "allowed_tool_categories": list(policy.allowed_tool_categories),
                "denied_tool_categories": list(policy.denied_tool_categories),
                "allowed_tools": list(policy.allowed_tools),
                "denied_tools": list(policy.denied_tools),
            },
        )
        prompt = self.prompt.compile(
            identity={"agent_id": policy.agent_id, "mode": policy.mode, "max_steps": policy.max_steps},
            observation=task,
            memory_view=memory_view,
            capability_view=capability_view,
            runtime_state={"step": 0, "preview": True},
        )
        runtime_ready_notes = [item.note_id for item in [*memory_view.system_cards, *memory_view.business_cards]]
        return {
            "task": task,
            "memory_view": asdict(memory_view),
            "capability_view": asdict(capability_view),
            "prompt": prompt,
            "runtime_ready_checks": [self.memory.check_runtime_ready(note_id) for note_id in runtime_ready_notes[:8]],
        }
