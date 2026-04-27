from __future__ import annotations

from kernel.prompt import PromptAssembler
from .normalizer import clip_text
from .types import PromptPacket, SurfaceSnapshot

TOOL_RESULT_ENVELOPE = '<tool_result tool="{tool}">\n{content}\n</tool_result>'


class PromptCompiler:
    """Compile MemoryView + CapabilityView into the model prompt."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel
        self.assembler = PromptAssembler()

    def compile(self, surface: SurfaceSnapshot) -> PromptPacket:
        system_prompt = self._budget(
            self.assembler.compile(
                identity={
                    "agent_id": self.kernel.agent.agent_id,
                    "engine_id": self.kernel.engine_id,
                    "active_skill": self.kernel.skill_state.active_skill_id,
                    "root_skill": self.kernel.skill_state.root_skill_id,
                    "provider": self.kernel.settings.provider,
                    "model": self.kernel.settings.model,
                    "max_steps": self.kernel.settings.max_steps,
                },
                observation=surface.observation,
                memory_view=surface.memory_view,
                capability_view=surface.capability_view,
                runtime_state=self._runtime_state_payload(),
            )
        )
        return PromptPacket(system_prompt=system_prompt, messages=self._messages())

    def _messages(self) -> list[dict]:
        rows = self.kernel.session.history.read()
        keep = self.kernel.settings.history_keep_turns
        messages: list[dict] = []
        for item in rows[-keep:]:
            role = item.get("role")
            content = str(item.get("content") or "")
            if role == "tool":
                messages.append({"role": "user", "content": TOOL_RESULT_ENVELOPE.format(tool=item.get("tool") or item.get("action"), content=content)})
            elif role == "system":
                messages.append({"role": "user", "content": f"<system_note>\n{content}\n</system_note>"})
            else:
                messages.append({"role": role, "content": content})
        return messages

    def _runtime_state_payload(self) -> dict:
        return {
            "step": self.kernel.runtime_state.step,
            "tool_results": [clip_text(item, limit=400) for item in self.kernel.runtime_state.tool_results[-4:]],
            "state_fragments": self.kernel.state_fragments(),
        }

    def _budget(self, text: str) -> str:
        return clip_text(text, limit=self.kernel.settings.max_prompt_chars)
