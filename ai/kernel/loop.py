from __future__ import annotations

from dataclasses import asdict

from capability.surface import CapabilitySurfaceResolver
from kernel.prompt import PromptAssembler
from kernel.state import AgentResult, Observation


class KernelPreviewLoop:
    """Preview-oriented Observe -> Orient -> Act -> Reflect -> Commit skeleton."""

    def __init__(self, *, memory, capability_registry, policy):  # noqa: ANN001
        self.memory = memory
        self.capability_registry = capability_registry
        self.policy = policy
        self.surface = CapabilitySurfaceResolver(capability_registry)
        self.prompt = PromptAssembler()

    def preview(self, task_brief: str) -> AgentResult:
        observation = Observation(task_brief=task_brief)
        memory_view = self.memory.orient(observation.task_brief)
        capability_view = self.surface.resolve(
            observation=observation.task_brief,
            memory_view=memory_view,
            policy={
                "tool_permission_level": self.policy.tool_permission_level,
                "allowed_tool_categories": list(self.policy.allowed_tool_categories),
                "denied_tool_categories": list(self.policy.denied_tool_categories),
                "allowed_tools": list(self.policy.allowed_tools),
                "denied_tools": list(self.policy.denied_tools),
            },
        )
        prompt = self.prompt.compile(
            identity={"agent_id": self.policy.agent_id, "mode": self.policy.mode, "max_steps": self.policy.max_steps},
            observation=observation.task_brief,
            memory_view=memory_view,
            capability_view=capability_view,
            runtime_state={"step": 0},
        )
        proposal = self.memory.capture(
            {
                "proposal_type": "runtime_hint",
                "source": "preview",
                "observation": observation.task_brief,
                "assistant_message": "preview-only",
                "tool_results": [],
                "memory_view": asdict(memory_view),
                "capability_view": asdict(capability_view),
            }
        )
        return AgentResult(reply=prompt, proposal=proposal, memory_view=memory_view, capability_view=capability_view)
