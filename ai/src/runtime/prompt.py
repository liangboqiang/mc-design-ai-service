from __future__ import annotations

import json

from .normalizer import clip_text
from .types import PromptPacket, SurfaceSnapshot

TOOL_RESULT_ENVELOPE = '<tool_result tool="{tool}">\n{content}\n</tool_result>'


class PromptCompiler:
    """Compile Wiki + ProtocolView + Surface into the model prompt."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel

    def compile(self, surface: SurfaceSnapshot) -> PromptPacket:
        sections: list[tuple[str, str]] = [
            ("Identity", self._identity()),
            ("Agent Wiki", self.kernel.context.agent_context or self.kernel.agent.context),
            ("Active Skill Wiki", self._active_skill_context()),
            ("Visible Skills", self._visible_skills(surface)),
            ("Visible Tools", self._visible_tools(surface)),
            ("Tool Visibility Reasons", self._visibility_reasons(surface)),
            ("Wiki Hub", self.kernel.wiki.system_brief()),
            ("Runtime State", self._state()),
            ("Response Contract", self._response_contract()),
        ]
        system_prompt = self._budget("\n\n".join(f"## {title}\n{body}" for title, body in sections if str(body).strip()))
        return PromptPacket(system_prompt=system_prompt, messages=self._messages())

    def _identity(self) -> str:
        return "\n".join([
            f"- agent: {self.kernel.agent.agent_id}",
            f"- engine_id: {self.kernel.engine_id}",
            f"- active_skill: {self.kernel.skill_state.active_skill_id}",
            f"- root_skill: {self.kernel.skill_state.root_skill_id}",
            f"- provider: {self.kernel.settings.provider}",
            f"- model: {self.kernel.settings.model}",
        ])

    def _active_skill_context(self) -> str:
        skill = self.kernel.skill_state.active_skill()
        return clip_text(skill.markdown_body or skill.context or skill.summary or skill.title, limit=3500)

    def _visible_skills(self, surface: SurfaceSnapshot) -> str:
        return "\n".join(f"- {sid}: {summary}" for sid, summary in surface.visible_skills) or "- (none)"

    def _visible_tools(self, surface: SurfaceSnapshot) -> str:
        rows: list[str] = []
        for spec in surface.visible_tools:
            rows.append(
                f"- `{spec.tool_id}`\n"
                f"  - description: {spec.description}\n"
                f"  - input_schema: {json.dumps(spec.input_schema, ensure_ascii=False)}\n"
                f"  - permission_level: {spec.permission_level}\n"
                f"  - categories: {', '.join(spec.categories or ())}\n"
                f"  - activation: {spec.activation_mode}\n"
                f"  - safety: {clip_text(spec.safety, limit=300) if spec.safety else '(not specified)'}"
            )
        return "\n".join(rows) or "- (none)"

    def _visibility_reasons(self, surface: SurfaceSnapshot) -> str:
        rows = []
        for reason in surface.reasons:
            if reason.visible:
                rows.append(f"- {reason.tool_id}: " + "; ".join(reason.reasons))
        return "\n".join(rows) or "- (none)"

    def _state(self) -> str:
        fragments = self.kernel.state_fragments()
        return "\n".join(fragments) if fragments else "(no extra state)"

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

    def _response_contract(self) -> str:
        return (
            "Return strict JSON only:\n"
            "{\n  \"assistant_message\": \"string\",\n  \"tool_calls\": [{\"tool\": \"tool.id\", \"arguments\": {}}]\n}\n"
            "Rules:\n"
            "1. Only call visible tools.\n"
            "2. Use `engine.enter_skill` when another visible child skill is more suitable.\n"
            "3. Prefer wiki tools when knowledge is needed.\n"
            "4. Keep assistant_message concise before tool use."
        )

    def _budget(self, text: str) -> str:
        return clip_text(text, limit=self.kernel.settings.max_prompt_chars)
