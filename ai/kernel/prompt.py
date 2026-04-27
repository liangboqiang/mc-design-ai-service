from __future__ import annotations

import json
from dataclasses import asdict


class PromptAssembler:
    def compile(
        self,
        *,
        identity: dict,
        observation: str,
        memory_view,
        capability_view,
        runtime_state: dict | None = None,
    ) -> str:
        sections = [
            ("Identity", self._identity(identity)),
            ("Task", observation.strip() or "(empty task)"),
            ("MemoryView", self._memory_view(memory_view)),
            ("CapabilityView", self._capability_view(capability_view)),
            ("RuntimeState", self._runtime_state(runtime_state or {})),
            ("ResponseContract", self._response_contract()),
        ]
        return "\n\n".join(f"## {title}\n{body}" for title, body in sections if str(body).strip())

    @staticmethod
    def _identity(identity: dict) -> str:
        return "\n".join(f"- {key}: {value}" for key, value in identity.items())

    @staticmethod
    def _memory_view(memory_view) -> str:  # noqa: ANN001
        payload = asdict(memory_view)
        rows = []
        rows.append("- system_cards:")
        rows.extend(f"  - {card['note_id']}: {card['summary']}" for card in payload.get("system_cards", []))
        rows.append("- business_cards:")
        rows.extend(f"  - {card['note_id']}: {card['summary']}" for card in payload.get("business_cards", []))
        rows.append("- constraints:")
        rows.extend(f"  - {item}" for item in payload.get("constraints", []))
        rows.append("- unknowns:")
        rows.extend(f"  - {item}" for item in payload.get("unknowns", []))
        rows.append("- activation_hints:")
        rows.extend(f"  - {item['capability_id']}: {item['reason']}" for item in payload.get("activation_hints", []))
        return "\n".join(rows)

    @staticmethod
    def _capability_view(capability_view) -> str:  # noqa: ANN001
        payload = asdict(capability_view)
        rows = []
        rows.append("- visible_skills:")
        rows.extend(f"  - {item['capability_id']}: {item['description']}" for item in payload.get("visible_skills", []))
        rows.append("- visible_tools:")
        rows.extend(
            f"  - {item['capability_id']}: permission={item['permission_level']}; categories={', '.join(item.get('categories') or [])}"
            for item in payload.get("visible_tools", [])
        )
        rows.append("- visible_workflows:")
        rows.extend(f"  - {item['capability_id']}: {item['description']}" for item in payload.get("visible_workflows", []))
        rows.append("- activation_reasons:")
        rows.extend(f"  - {item}" for item in payload.get("activation_reasons", []))
        rows.append("- denied_reasons:")
        rows.extend(f"  - {item}" for item in payload.get("denied_reasons", []))
        return "\n".join(rows)

    @staticmethod
    def _runtime_state(runtime_state: dict) -> str:
        if not runtime_state:
            return "- step: 0"
        return json.dumps(runtime_state, ensure_ascii=False, indent=2)

    @staticmethod
    def _response_contract() -> str:
        return (
            "Return strict JSON only:\n"
            "{\n"
            '  "assistant_message": "string",\n'
            '  "tool_calls": [{"tool": "tool.id", "arguments": {}}],\n'
            '  "memory_requests": [],\n'
            '  "proposal_hints": []\n'
            "}\n"
            "Rules:\n"
            "1. Only call visible tools.\n"
            "2. Prefer capabilities explicitly activated by MemoryView.\n"
            "3. Keep assistant_message concise before tool use."
        )
