from __future__ import annotations


def build_extraction_prompt(
    *,
    source_kind: str,
    source_path: str,
    source_uri: str,
    chunk_index: int,
    chunk_count: int,
    content: str,
) -> str:
    return f"""
You are a wiki extraction worker.
Your only job is to convert one source chunk into a structured wiki page draft.

Return ONLY a JSON object string in your assistant_message with these keys:
- title: string
- summary: string
- key_points: array of short strings
- tags: array of strings

Rules:
- Do not call any tools.
- Be concise and factual.
- Prefer architecture and usage meaning over raw code restatement.
- If the source is code, summarize responsibility, main interfaces, and important constraints.
- Do not include markdown fences.

Source kind: {source_kind}
Source path: {source_path}
Source uri: {source_uri}
Chunk: {chunk_index}/{chunk_count}

Source content:
{content}
""".strip()
