from __future__ import annotations

from .turn import TurnLoop


class Engine:
    """Thin runtime facade over RuntimeKernel."""

    def __init__(self, kernel):
        self.kernel = kernel

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        return TurnLoop(self.kernel).run(message, files=files)

    def tick(self) -> str:
        autonomy = self.kernel.runtime_state.installed_toolboxes.get("autonomy")
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not result.startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return result

    def spawn_child(
        self,
        *,
        skill: str | None,
        role_name: str,
        tools: list[str] | None = None,
        enhancements: list[str] | None = None,
        toolboxes: list[str] | None = None,
    ):
        from .types import RuntimeRequest
        from .bootstrap import RuntimeBootstrap

        target_skill = self.kernel.skill_state.active_skill_id if skill in (None, "", "root") else self.kernel.skill_state.resolve_skill_alias(skill)
        child_agent = self.kernel.agent
        request = RuntimeRequest(
            agent_id=child_agent.agent_id,
            project_root=self.kernel.registry.project_root,
            provider=self.kernel.settings.provider,
            model=self.kernel.settings.model,
            api_key=self.kernel.settings.api_key,
            base_url=self.kernel.settings.base_url,
            user_id=self.kernel.settings.user_id,
            conversation_id=self.kernel.settings.conversation_id,
            task_id=f"{self.kernel.settings.task_id}__{role_name}",
            toolboxes=tools or toolboxes or enhancements or child_agent.installation_names(),
            storage_base=self.kernel.session.paths.root.parents[2],
            role_name=role_name,
            policy={"max_prompt_chars": max(6000, self.kernel.settings.max_prompt_chars // 2)},
        )
        child = RuntimeBootstrap().build(request)
        child.kernel.skill_state.active_skill_id = target_skill
        return child
