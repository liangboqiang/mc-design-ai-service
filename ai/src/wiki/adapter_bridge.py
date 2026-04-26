from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Iterable

from .node import WikiNode
from .page_parser import compile_runtime_from_chinese, extract_link_targets


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CODE_RE = re.compile(r"`([^`]+)`")


SECTION_ALIASES = {
    "overview": {"overview", "summary", "简介", "摘要", "说明", "背景", "上下文", "内容", "context"},
    "capabilities": {"capabilities", "能力", "功能", "支持能力"},
    "usage": {"usage", "use", "使用方式", "适用场景", "何时使用", "工具说明", "技能目标", "智能体使命", "context hint"},
    "runtime": {"runtime", "运行时", "协议", "协议字段", "基本信息", "system", "系统字段"},
    "tools": {"tools", "tool", "工具", "可用工具", "调用工具", "能力工具", "使用工具", "包含工具", "可用技能", "可用工具箱"},
    "links": {"links", "refs", "related", "related pages", "相关", "引用", "关联节点", "关联页面"},
    "root": {"root", "root skill", "根技能"},
    "children": {"child nodes", "child skills", "children", "子技能", "下级技能", "下级页面"},
    "policy": {"policy", "策略", "权限", "permission", "activation"},
    "input": {"input", "schema", "参数", "输入", "入参", "输入说明"},
    "output": {"output", "返回", "输出", "出参", "输出说明"},
    "safety": {"safety", "安全", "边界", "约束", "风险", "注意事项", "安全边界", "使用边界"},
    "toolbox": {"toolbox", "toolboxes", "工具箱"},
    "category": {"category", "categories", "分类"},
}


def normalize_section_title(title: str) -> str:
    raw = title.strip()
    low = raw.lower()
    for canonical, aliases in SECTION_ALIASES.items():
        if low in aliases or raw in aliases:
            return canonical
    return low


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.strip().startswith("# "):
            return line.strip()[2:].strip() or fallback
    return fallback.replace("_", " ").replace("-", " ").title()


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 2:
            current = normalize_section_title(match.group(2))
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if key != "__root__" and "\n".join(value).strip()}


def first_paragraph(text: str) -> str:
    rows: list[str] = []
    started = False
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("- [["):
            if started:
                break
            continue
        if s.startswith("```"):
            continue
        started = True
        rows.append(s)
    return " ".join(rows)[:400].strip()


def extract_runtime_block(sections: dict[str, str], text: str = "") -> dict[str, object]:
    legacy_body = sections.get("runtime", "")
    legacy = _extract_fenced_runtime(legacy_body) or _extract_bullet_runtime(legacy_body)
    chinese = compile_runtime_from_chinese(text) if text else {}
    payload = dict(legacy)
    payload.update(chinese)
    return payload


def _extract_fenced_runtime(body: str) -> dict[str, object]:
    match = re.search(r"```(?:yaml|yml|json)\s*(.*?)```", body, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return {}
    raw = textwrap.dedent(match.group(1)).strip()
    if not raw:
        return {}
    if match.group(0).lower().startswith("```json"):
        try:
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}
    return _parse_simple_yaml(raw)


def _parse_simple_yaml(raw: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    current_key = ""
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if ":" in stripped and not stripped.startswith("- "):
            key, value = stripped.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value:
                payload[current_key] = _clean_value(value)
            else:
                payload[current_key] = []
            continue
        if current_key and stripped.startswith("- "):
            payload.setdefault(current_key, [])
            if isinstance(payload[current_key], list):
                payload[current_key].append(_clean_value(stripped[2:].strip()))
    return payload


def _extract_bullet_runtime(body: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    current_key = ""
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("- "):
            item = s[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current_key = key.strip()
                value = value.strip().strip("`")
                if value:
                    payload[current_key] = _clean_value(value)
                else:
                    payload[current_key] = []
            elif current_key:
                payload.setdefault(current_key, [])
                if isinstance(payload[current_key], list):
                    payload[current_key].append(_clean_value(item.strip("`")))
        elif current_key and s.startswith("  - "):
            payload.setdefault(current_key, [])
            if isinstance(payload[current_key], list):
                payload[current_key].append(_clean_value(s[4:].strip("`")))
    return payload


def _clean_value(value: str) -> object:
    value = value.strip().strip('"').strip("'")
    if value.startswith("[[") and value.endswith("]]"):
        return value[2:-2].strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_clean_value(item.strip()) for item in inner.split(",")]
    if value.isdigit():
        return int(value)
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


class WikiAdapterBridge:
    """Single node stream for system Wiki Pages and materialized Wiki Store nodes."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.src_root = self.project_root / "src"

    def iter_nodes(self) -> list[WikiNode]:
        nodes: list[WikiNode] = []
        for path in sorted(self.src_root.rglob("*.md")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(self.project_root).as_posix()
            if rel.startswith("src/wiki/store/") or rel.startswith("src/wiki/workbench/store/"):
                continue
            text = path.read_text(encoding="utf-8")
            sections = split_sections(text)
            node_id = self._node_id(path)
            nodes.append(
                WikiNode(
                    node_id=node_id,
                    title=extract_title(text, path.parent.name),
                    body=text,
                    summary=first_paragraph(text),
                    source_path=rel,
                    source_type="system",
                    node_kind_hint=self._kind_hint(path),
                    links=extract_link_targets(text),
                    sections=sections,
                    runtime_block=extract_runtime_block(sections, text),
                )
            )
        return nodes

    def _node_id(self, path: Path) -> str:
        rel_folder = path.parent.relative_to(self.src_root).as_posix()
        if path.name == "wiki.md":
            return rel_folder
        return f"wiki/{path.relative_to(self.src_root).as_posix()}"

    def _kind_hint(self, path: Path) -> str:
        parts = path.parent.relative_to(self.src_root).parts
        if not parts:
            return "knowledge"
        if parts[0] == "agent":
            return "agent"
        if parts[0] == "skill":
            return "skill"
        if parts[0] == "tool":
            if len(parts) >= 2 and parts[1] == "wiki":
                return "toolbox" if len(parts) == 2 else "tool"
            if len(parts) >= 3 and parts[1] in {"external", "workflow", "system"}:
                return "toolbox" if len(parts) == 3 else "tool"
            return "tool"
        if parts[0] == "wiki":
            return "knowledge"
        return parts[0]
