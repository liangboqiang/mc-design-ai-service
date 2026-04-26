from __future__ import annotations

from wiki.page_state import is_disabled_markdown, is_locked_markdown

from collections.abc import Callable


class WikiSearcher:
    def __init__(self, *, store, read_text: Callable[[str], str]):  # noqa: ANN001
        self.store = store
        self.read_text = read_text

    def search(self, query: str, *, limit: int = 20) -> list[dict]:
        self.store.ensure()
        query = str(query or "").strip().lower()
        limit = max(1, int(limit or 20))
        pages = self.store.read_catalog().get("pages") or {}

        scored: list[tuple[int, dict]] = []
        tokens = [token for token in query.split() if token]
        for page_id, row in pages.items():
            body = self.read_text(str(row.get("path") or ""))
            summary = str(row.get("summary") or "").strip()
            disabled = bool(row.get("disabled")) or is_disabled_markdown(body)
            locked = bool(row.get("locked")) or is_locked_markdown(body)
            haystack = " ".join(
                [str(row.get("title") or ""), str(row.get("path") or ""), summary, body[:4000]]
            ).lower()
            score = sum(haystack.count(token) for token in tokens) if tokens else 1
            if score > 0 or not tokens:
                scored.append(
                    (
                        score,
                        {
                            "page_id": page_id,
                            "title": row.get("title"),
                            "path": row.get("path"),
                            "score": score,
                            "summary": summary or body[:400],
                            "locked": locked,
                            "disabled": disabled,
                        },
                    )
                )

        scored.sort(key=lambda item: (-item[0], str(item[1].get("title") or "")))
        return [row for _, row in scored[:limit]]
