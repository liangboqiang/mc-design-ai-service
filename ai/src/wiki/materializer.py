from __future__ import annotations

from datetime import datetime

from .models import WikiPage


def build_page_markdown(page: WikiPage) -> str:
    meta_tags = ", ".join(page.tags)
    bullets = "\n".join(f"- {item}" for item in page.key_points) if page.key_points else "- (none)"
    return f"""---
page_id: {page.page_id}
source_id: {page.source_id}
source_kind: {page.source_kind}
source_path: {page.source_path}
source_uri: {page.source_uri}
source_hash: {page.source_hash}
updated_at: {page.updated_at}
tags: [{meta_tags}]
---

# {page.title}

## Summary

{page.summary}

## Key Points

{bullets}

## Source

- Path: `{page.source_path}`
- URI: `{page.source_uri}`
- Hash: `{page.source_hash}`
"""


def make_page(
    *,
    page_id: str,
    source_id: str,
    source_kind: str,
    source_path: str,
    source_uri: str,
    source_hash: str,
    payload: dict,
    tags: list[str],
) -> WikiPage:
    merged_tags = [str(item).strip() for item in [*tags, *(payload.get("tags") or [])] if str(item).strip()]
    merged_tags = list(dict.fromkeys(merged_tags))
    key_points = [str(item).strip() for item in payload.get("key_points") or [] if str(item).strip()]
    return WikiPage(
        page_id=page_id,
        source_id=source_id,
        title=str(payload.get("title") or source_path),
        summary=str(payload.get("summary") or "").strip(),
        key_points=key_points,
        source_kind=source_kind,
        source_path=source_path,
        source_uri=source_uri,
        source_hash=source_hash,
        tags=merged_tags,
        updated_at=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        metadata={},
    )
