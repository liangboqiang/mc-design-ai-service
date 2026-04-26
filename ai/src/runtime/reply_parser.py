from __future__ import annotations

import json
import re
import uuid

from protocol.types import LLMResponse, ToolCall


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class ReplyParser:
    @staticmethod
    def parse(raw_text: str) -> LLMResponse:
        raw_text = str(raw_text or "").strip()
        candidate = raw_text
        match = JSON_BLOCK_RE.search(raw_text)
        if match:
            candidate = match.group(1)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            first = raw_text.find("{")
            last = raw_text.rfind("}")
            if first >= 0 and last > first:
                payload = json.loads(raw_text[first : last + 1])
            else:
                return LLMResponse(assistant_message=raw_text, tool_calls=[], raw_text=raw_text)
        calls = [
            ToolCall(str(uuid.uuid4())[:8], str(call["tool"]), dict(call.get("arguments") or {}))
            for call in payload.get("tool_calls", [])
        ]
        return LLMResponse(str(payload.get("assistant_message") or ""), calls, raw_text)
