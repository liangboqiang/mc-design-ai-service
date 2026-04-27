from __future__ import annotations

import json
import re


CALL_RE = re.compile(r"^/tool\s+(?P<tool>[\w\.-]+)(?:\s+(?P<args>\{.*\}))?\s*$", re.DOTALL)
SKILL_RE = re.compile(r"^/skill\s+(?P<skill>.+)$")
TOOL_RESULT_RE = re.compile(r"<tool_result tool=\"(?P<tool>[^\"]+)\">\n(?P<body>.*?)\n</tool_result>", re.DOTALL)


class MockClient:
    def __init__(self, model: str = "mock"):
        self.model = model

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        latest = messages[-1]["content"].strip()
        call_match = CALL_RE.match(latest)
        if call_match:
            args = json.loads(call_match.group("args") or "{}")
            return json.dumps(
                {
                    "assistant_message": "",
                    "tool_calls": [{"tool": call_match.group("tool"), "arguments": args}],
                },
                ensure_ascii=False,
            )

        skill_match = SKILL_RE.match(latest)
        if skill_match:
            return json.dumps(
                {
                    "assistant_message": "",
                    "tool_calls": [
                        {"tool": "engine.enter_skill", "arguments": {"skill": skill_match.group("skill").strip()}}
                    ],
                },
                ensure_ascii=False,
            )

        tool_result_match = TOOL_RESULT_RE.fullmatch(latest)
        if tool_result_match:
            return json.dumps(
                {
                    "assistant_message": tool_result_match.group("body").strip(),
                    "tool_calls": [],
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "assistant_message": f"[mock:{self.model}] {latest}",
                "tool_calls": [],
            },
            ensure_ascii=False,
        )
