from __future__ import annotations


class MemoryCurator:
    """Lightweight placeholder for future LLM-assisted memory curation."""

    @staticmethod
    def summarize(text: str, *, limit: int = 320) -> str:
        flat = " ".join(part.strip() for part in str(text or "").splitlines() if part.strip())
        return flat[:limit].strip()
