from __future__ import annotations

import json
import re
import uuid
from typing import Any

from kernel.state import ParsedReply, ToolCall

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class KernelReplyParser:
    @staticmethod
    def parse(raw_text: str) -> ParsedReply:
        raw_text = str(raw_text or "").strip()
        candidate = raw_text
        match = JSON_BLOCK_RE.search(raw_text)
        if match:
            candidate = match.group(1)
        try:
            payload: dict[str, Any] = json.loads(candidate)
        except json.JSONDecodeError:
            first = raw_text.find("{")
            last = raw_text.rfind("}")
            if first >= 0 and last > first:
                try:
                    payload = json.loads(raw_text[first : last + 1])
                except json.JSONDecodeError:
                    return ParsedReply(assistant_message=raw_text, tool_calls=[], raw_text=raw_text)
            else:
                return ParsedReply(assistant_message=raw_text, tool_calls=[], raw_text=raw_text)
        calls = []
        for call in payload.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            tool = str(call.get("tool") or call.get("capability_id") or "").strip()
            if not tool:
                continue
            calls.append(ToolCall(str(call.get("call_id") or uuid.uuid4().hex[:8]), tool, dict(call.get("arguments") or {})))
        return ParsedReply(
            assistant_message=str(payload.get("assistant_message") or ""),
            tool_calls=calls,
            raw_text=raw_text,
            memory_requests=list(payload.get("memory_requests") or []),
            proposal_hints=list(payload.get("proposal_hints") or []),
        )
