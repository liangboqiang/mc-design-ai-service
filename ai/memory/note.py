from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from memory.types import MemoryNote, RelationHint
from workspace_paths import data_root, src_root, workspace_root

try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None

try:
    from wiki.adapter_bridge import extract_runtime_block
except Exception:  # noqa: BLE001
    extract_runtime_block = None


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SECTION_ALIASES = {
    "summary": {"summary", "overview", "简介", "摘要"},
    "fields": {"fields", "field", "基本信息", "元字段"},
    "relations": {"relations", "relation", "links", "关联关系", "关系"},
    "evidence": {"evidence", "来源", "证据"},
    "runtime_notes": {"runtime notes", "runtime", "运行说明", "运行时"},
}
FRONTMATTER_RESERVED = {"id", "kind", "status", "maturity", "lens", "source_refs", "tags", "title", "fields"}
KIND_HINTS = {
    "agent": "Agent",
    "skill": "Skill",
    "tool": "Tool",
    "toolbox": "Toolbox",
    "workflow": "Workflow",
    "policy": "Policy",
    "rule": "Rule",
    "document": "Document",
    "case": "Case",
    "part": "Part",
    "parameter": "Document",
    "wiki": "Document",
    "knowledge": "Document",
}


def parse_note_file(project_root: Path, path: Path) -> MemoryNote:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    sections = _split_sections(body)
    title = str(meta.get("title") or _extract_title(body, path.parent.name))
    fields = _build_fields(meta, sections, body)
    source_refs = _ensure_list(meta.get("source_refs")) or _extract_evidence_refs(sections.get("evidence", ""))
    tags = [str(item) for item in _ensure_list(meta.get("tags"))]
    note_id = str(meta.get("id") or _derive_note_id(project_root, path))
    kind = str(meta.get("kind") or _derive_kind(project_root, path, fields)).strip() or "Document"
    status = str(meta.get("status") or _default_status(path)).strip() or "draft"
    maturity = str(meta.get("maturity") or _default_maturity(status, kind)).strip() or "draft"
    relations = _parse_relations(sections.get("relations", ""), status=status)
    links = _extract_links(body)
    summary = _extract_summary(body, sections)
    base_root = workspace_root(project_root)
    if project_root in [path.parent, *path.parents]:
        path_value = path.relative_to(project_root).as_posix()
    else:
        path_value = path.relative_to(base_root).as_posix()
    return MemoryNote(
        note_id=note_id,
        title=title,
        kind=kind,
        status=status,
        body=body,
        fields=fields,
        relations=relations,
        source_refs=source_refs,
        tags=tags,
        maturity=maturity,
        path=path_value,
        summary=summary,
        links=links,
        lens_id=str(meta.get("lens") or _default_lens_id(kind)),
        sections=sections,
    )


def render_note_markdown(note: MemoryNote) -> str:
    lines = ["---"]
    lines.append(f"id: {note.note_id}")
    lines.append(f"kind: {_display_kind(note.kind)}")
    lines.append(f"status: {note.status}")
    lines.append(f"maturity: {note.maturity}")
    if note.lens_id:
        lines.append(f"lens: {note.lens_id}")
    lines.append("source_refs:")
    if note.source_refs:
        lines.extend(f"  - {item}" for item in note.source_refs)
    else:
        lines.append("  - legacy.wiki.compat")
    lines.append("tags:")
    if note.tags:
        lines.extend(f"  - {item}" for item in note.tags)
    else:
        lines.append("  - migrated")
    lines.append("---")
    lines.append("")
    lines.append(note.body.strip())
    lines.append("")
    return "\n".join(lines)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1).strip()
    body = text[match.end() :]
    if not raw:
        return {}, body
    if yaml is not None:
        try:
            payload = yaml.safe_load(raw) or {}
            return payload if isinstance(payload, dict) else {}, body
        except Exception:  # noqa: BLE001
            pass
    return _parse_simple_yaml(raw), body


def _parse_simple_yaml(raw: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    current_key = ""
    for line in raw.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        if ":" in stripped and not stripped.lstrip().startswith("- "):
            key, value = stripped.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            payload[current_key] = _clean_value(value) if value else []
            continue
        if current_key and stripped.lstrip().startswith("- "):
            payload.setdefault(current_key, [])
            if isinstance(payload[current_key], list):
                payload[current_key].append(_clean_value(stripped.split("- ", 1)[1].strip()))
    return payload


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 2:
            current = _normalize_section_name(match.group(2))
            sections.setdefault(current, [])
            continue
        if current:
            sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


def _normalize_section_name(name: str) -> str:
    raw = name.strip()
    low = raw.lower()
    for canonical, aliases in SECTION_ALIASES.items():
        if low in aliases or raw in aliases:
            return canonical
    return low.replace(" ", "_")


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("# "):
            return line.strip()[2:].strip() or fallback
    return fallback.replace("_", " ").replace("-", " ").title()


def _extract_summary(text: str, sections: dict[str, str]) -> str:
    if sections.get("summary"):
        return _compact_text(sections["summary"], limit=320)
    rows: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            if rows:
                break
            continue
        rows.append(stripped)
    return _compact_text(" ".join(rows), limit=320)


def _build_fields(meta: dict[str, Any], sections: dict[str, str], body: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    from_meta = meta.get("fields")
    if isinstance(from_meta, dict):
        fields.update(from_meta)
    for key, value in meta.items():
        if key not in FRONTMATTER_RESERVED:
            fields.setdefault(str(key), value)
    fields.update(_parse_field_lines(sections.get("fields", "")))
    if extract_runtime_block is not None:
        try:
            runtime_block = extract_runtime_block(sections, body) or {}
        except Exception:  # noqa: BLE001
            runtime_block = {}
        for key, value in runtime_block.items():
            fields.setdefault(str(key), value)
    return fields


def _parse_field_lines(body: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    current_key = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if "：" in item:
                key, value = item.split("：", 1)
                current_key = key.strip()
                payload[current_key] = _clean_value(value.strip())
            elif ":" in item:
                key, value = item.split(":", 1)
                current_key = key.strip()
                payload[current_key] = _clean_value(value.strip())
            elif current_key:
                payload.setdefault(current_key, [])
                if isinstance(payload[current_key], list):
                    payload[current_key].append(_clean_value(item))
        elif current_key and stripped.startswith("  - "):
            payload.setdefault(current_key, [])
            if isinstance(payload[current_key], list):
                payload[current_key].append(_clean_value(stripped[4:].strip()))
    return payload


def _parse_relations(body: str, *, status: str) -> list[RelationHint]:
    rows: list[RelationHint] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        item = stripped[2:].strip()
        if "：" in item:
            predicate, value = item.split("：", 1)
        elif ":" in item:
            predicate, value = item.split(":", 1)
        else:
            continue
        predicate = predicate.strip()
        targets = _parse_targets(value)
        edge_status = _status_to_edge_status(status)
        for target in targets:
            rows.append(
                RelationHint(
                    predicate=predicate,
                    target=target,
                    label=predicate,
                    kind="declared",
                    status=edge_status,
                    confidence=1.0,
                    evidence=item,
                    source_field=f"Relations.{predicate}",
                )
            )
    return rows


def _extract_evidence_refs(body: str) -> list[str]:
    refs: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        item = stripped[2:].strip()
        refs.extend(_parse_targets(item))
    return _unique(refs)


def _extract_links(text: str) -> list[str]:
    targets: list[str] = []
    for raw in LINK_RE.findall(text):
        label = raw.strip()
        if not label:
            continue
        if "|" in label:
            _, label = label.split("|", 1)
        targets.append(label.strip())
    return _unique(targets)


def _parse_targets(value: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    matches = _extract_links(raw)
    if matches:
        return matches
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("`") for item in inner.split(",") if item.strip()]
    if "、" in raw:
        return [item.strip().strip("`") for item in raw.split("、") if item.strip()]
    if "," in raw:
        return [item.strip().strip("`") for item in raw.split(",") if item.strip()]
    return [raw.strip().strip("`")]


def _clean_value(value: str) -> Any:
    raw = value.strip().strip("`").strip('"').strip("'")
    if not raw:
        return ""
    if raw.startswith("{") and raw.endswith("}"):
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload
        except Exception:  # noqa: BLE001
            pass
    if raw.startswith("[[") and raw.endswith("]]"):
        return raw[2:-2].strip()
    if raw.startswith("[") and raw.endswith("]"):
        return _parse_targets(raw)
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    if raw.isdigit():
        return int(raw)
    if "、" in raw:
        return [item.strip() for item in raw.split("、") if item.strip()]
    if "," in raw and "http" not in raw and "\\" not in raw and "/" not in raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    return raw


def _derive_note_id(project_root: Path, path: Path) -> str:
    source_root = src_root(project_root)
    data_notes_root = data_root(project_root) / "notes"
    if source_root in [path.parent, *path.parents]:
        if path.name in {"note.md", "wiki.md"}:
            return path.parent.relative_to(source_root).as_posix()
        return path.relative_to(source_root).with_suffix("").as_posix().replace("/", ".")
    if data_notes_root in [path.parent, *path.parents]:
        rel = path.relative_to(data_notes_root)
        if path.name in {"note.md", "wiki.md"}:
            rel = rel.parent
        else:
            rel = rel.with_suffix("")
        return ".".join(part for part in rel.parts if part)
    return path.stem


def _derive_kind(project_root: Path, path: Path, fields: dict[str, Any]) -> str:
    for key in ("kind", "type", "entity_type"):
        value = fields.get(key)
        if isinstance(value, str) and value.strip():
            return str(value).strip()
    source_root = src_root(project_root)
    data_notes_root = data_root(project_root) / "notes"
    rel_parts = ()
    if source_root in [path.parent, *path.parents]:
        rel_parts = path.relative_to(source_root).parts
    elif data_notes_root in [path.parent, *path.parents]:
        rel_parts = path.relative_to(data_notes_root).parts
    if path.name in {"note.md", "wiki.md"} and path.parent.name and (path.parent / "toolbox.py").exists():
        return "Toolbox"
    for part in rel_parts:
        hint = KIND_HINTS.get(part.lower())
        if hint:
            return hint
    return "Document"


def _default_status(path: Path) -> str:
    return "published" if path.name == "wiki.md" else "draft"


def _default_maturity(status: str, kind: str) -> str:
    if status in {"published", "projectable", "runtime_ready", "locked"}:
        return "runtime_ready" if kind in {"Agent", "Skill", "Tool", "Toolbox", "Workflow"} else "projectable"
    if status == "reviewed":
        return "reviewed"
    return "draft"


def _default_lens_id(kind: str) -> str:
    normalized = kind.strip().lower() or "default"
    if normalized in {"agent", "skill", "tool", "part"}:
        return f"lens.{normalized}"
    if normalized in {"document", "case", "policy", "rule"}:
        return "lens.business_doc"
    return "lens.default"


def _display_kind(kind: str) -> str:
    normalized = str(kind or "").strip().lower()
    return {
        "agent": "Agent",
        "skill": "Skill",
        "tool": "Tool",
        "toolbox": "Toolbox",
        "workflow": "Workflow",
        "policy": "Policy",
        "rule": "Rule",
        "document": "Document",
        "case": "Case",
        "part": "Part",
    }.get(normalized, kind or "Document")


def _status_to_edge_status(status: str) -> str:
    if status in {"published", "projectable", "runtime_ready", "locked"}:
        return "published"
    if status == "reviewed":
        return "reviewed"
    if status == "rejected":
        return "rejected"
    return "candidate"


def _compact_text(text: str, *, limit: int) -> str:
    flat = " ".join(part.strip() for part in str(text or "").splitlines() if part.strip())
    return flat[:limit].strip()


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        normalized = str(item).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
