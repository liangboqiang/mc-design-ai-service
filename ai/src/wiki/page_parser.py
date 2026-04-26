from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .lexicon import FIELD_ALIASES, normalize_list, normalize_scalar, strip_link

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

@dataclass(slots=True)
class WikiPageModel:
    entity_type: str = ""
    entity_name: str = ""
    unique_id: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
    links: list[str] = field(default_factory=list)

def parse_chinese_page(text: str) -> WikiPageModel:
    sections = split_sections(text)
    title = extract_title(text)
    entity_type, entity_name = split_title(title)
    fields = extract_fields(sections)
    if not entity_type:
        entity_type = str(fields.get("实体类型") or "")
    if not entity_name:
        entity_name = str(fields.get("实体名称") or "")
    unique_id = str(fields.get("唯一标识") or "").strip()
    return WikiPageModel(
        entity_type=entity_type,
        entity_name=entity_name,
        unique_id=unique_id,
        fields=fields,
        sections=sections,
        links=extract_link_targets(text),
    )

def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 2:
            current = match.group(2).strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if key != "__root__" and "\n".join(value).strip()}

def extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("# "):
            return line.strip()[2:].strip()
    return ""

def split_title(title: str) -> tuple[str, str]:
    if "：" in title:
        left, right = title.split("：", 1)
        return left.strip(), right.strip()
    if ":" in title:
        left, right = title.split(":", 1)
        return left.strip(), right.strip()
    return "", title.strip()

def extract_fields(sections: dict[str, str]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for section_name in ("基本信息", "元词条", "协议字段", "版本信息"):
        body = sections.get(section_name, "")
        current_key = ""
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("- ") and "：" in stripped:
                key, value = stripped[2:].split("：", 1)
                current_key = key.strip()
                fields[current_key] = clean_value(value.strip())
            elif stripped.startswith("- ") and ":" in stripped:
                key, value = stripped[2:].split(":", 1)
                current_key = key.strip()
                fields[current_key] = clean_value(value.strip())
            elif current_key and stripped.startswith("  - "):
                fields.setdefault(current_key, [])
                if not isinstance(fields[current_key], list):
                    fields[current_key] = [str(fields[current_key])]
                fields[current_key].append(clean_value(stripped[4:].strip()))
    return fields

def clean_value(value: str):
    value = value.strip()
    if value in {"", "无", "待补充"}:
        return value
    if "、" in value:
        return [item.strip() for item in value.split("、") if item.strip()]
    if "," in value and not value.startswith("[["):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value.strip("`")

def compile_runtime_from_chinese(text: str) -> dict[str, Any]:
    model = parse_chinese_page(text)
    fields = model.fields
    runtime: dict[str, Any] = {}
    if model.entity_type:
        runtime["type"] = normalize_scalar(model.entity_type)
    if model.unique_id:
        runtime["id"] = normalize_scalar(model.unique_id)

    for chinese_key, protocol_key in FIELD_ALIASES.items():
        if chinese_key not in fields:
            continue
        value = fields[chinese_key]
        if isinstance(value, list):
            runtime[protocol_key] = normalize_list([str(item) for item in value])
        else:
            runtime[protocol_key] = normalize_scalar(str(value))

    if "categories" in runtime and isinstance(runtime["categories"], str):
        runtime["categories"] = normalize_list([runtime["categories"]])
    if "toolboxes" in runtime and isinstance(runtime["toolboxes"], str):
        runtime["toolboxes"] = normalize_list([runtime["toolboxes"]])
    if "allowed_tool_categories" in runtime and isinstance(runtime["allowed_tool_categories"], str):
        runtime["allowed_tool_categories"] = normalize_list([runtime["allowed_tool_categories"]])
    if "denied_tool_categories" in runtime and isinstance(runtime["denied_tool_categories"], str):
        runtime["denied_tool_categories"] = normalize_list([runtime["denied_tool_categories"]])
    if "denied_tools" in runtime and isinstance(runtime["denied_tools"], str):
        runtime["denied_tools"] = normalize_list([runtime["denied_tools"]])

    return {k: v for k, v in runtime.items() if v not in ("", "待补充", [], None)}

def extract_link_targets(text: str) -> list[str]:
    targets: list[str] = []
    for raw in LINK_RE.findall(text):
        raw = raw.strip()
        if "|" in raw:
            _, target = raw.split("|", 1)
            targets.append(target.strip())
        else:
            targets.append(raw)
    return sorted(dict.fromkeys(targets))
