from __future__ import annotations

import hashlib
from pathlib import Path

from shared.ids import new_id

from ..models import WikiTask
from ..prompts import build_extraction_prompt
from ..source_policy import WikiSourcePolicy


def chunk_text(text: str, *, chunk_chars: int = 12000, overlap: int = 500) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_chars)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def plan_registry_tasks(project_root: Path, registry, extractor_skill: str) -> list[WikiTask]:  # noqa: ANN001
    policy = WikiSourcePolicy()
    rows = []
    for path in registry.iter_business_source_files():
        rows.append(Path(path).resolve())
    for path in registry.iter_system_source_files():
        rows.append(Path(path).resolve())
    seen: set[Path] = set()
    tasks: list[WikiTask] = []
    for path in sorted(rows):
        if path in seen or not path.exists() or not path.is_file():
            continue
        seen.add(path)
        include, kind, tags = policy.include(project_root, path)
        if not include:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(project_root).as_posix()
        source_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()
        chunks = chunk_text(text)
        for chunk_index, chunk in enumerate(chunks, start=1):
            source_id = f"{rel}#{chunk_index}"
            page_id = hashlib.sha1(source_id.encode("utf-8")).hexdigest()[:16]
            prompt = build_extraction_prompt(
                source_kind=kind,
                source_path=rel,
                source_uri=f"file://{path.as_posix()}",
                chunk_index=chunk_index,
                chunk_count=len(chunks),
                content=chunk,
            )
            tasks.append(
                WikiTask(
                    task_id=new_id("wiki_task"),
                    page_id=page_id,
                    source_id=source_id,
                    source_path=rel,
                    source_uri=f"file://{path.as_posix()}",
                    source_kind=kind,
                    title_hint=path.stem,
                    prompt=prompt,
                    tags=list(tags),
                    metadata={"source_hash": source_hash, "extractor_skill": extractor_skill},
                )
            )
    return tasks
