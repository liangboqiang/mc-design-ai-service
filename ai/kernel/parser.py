from __future__ import annotations

import json
import re


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class KernelReplyParser:
    @staticmethod
    def parse(raw_text: str) -> dict:
        raw_text = str(raw_text or "").strip()
        candidate = raw_text
        match = JSON_BLOCK_RE.search(raw_text)
        if match:
            candidate = match.group(1)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return {"assistant_message": raw_text, "tool_calls": [], "memory_requests": [], "proposal_hints": []}
        payload.setdefault("assistant_message", "")
        payload.setdefault("tool_calls", [])
        payload.setdefault("memory_requests", [])
        payload.setdefault("proposal_hints", [])
        return payload
