from __future__ import annotations


def clip_text(text: str, *, limit: int = 8000) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


class Normalizer:
    def normalize_tool_result(self, tool_id: str, result: str, *, limit: int = 8000) -> str:
        return clip_text(result, limit=limit)

    def normalize_state_fragments(self, fragments: list[str]) -> list[str]:
        seen: set[str] = set()
        rows: list[str] = []
        for item in fragments:
            text = str(item).strip()
            if text and text not in seen:
                seen.add(text)
                rows.append(text)
        return rows
