from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import yaml

from wiki.adapter_bridge import LINK_RE, extract_title as extract_markdown_title, first_paragraph, split_sections as split_markdown_sections

def extract_markdown_links(text: str) -> list[str]:
    return [item.strip() for item in LINK_RE.findall(text) if item.strip()]

def extract_section_code_items(text: str) -> list[str]:
    import re
    rows = [item.strip() for item in re.findall(r"`([^`]+)`", text) if item.strip()]
    if rows:
        return rows
    return [line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]


from .config import WikiConfig

_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^[-*]\s+(.+)$", re.MULTILINE)


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_text(path: Path, *, limit: int) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit]


def summarize_file(path: Path, relpath: str, *, kind: str, config: WikiConfig) -> tuple[str, list[str], str, dict]:
    suffix = path.suffix.lower()
    text = _safe_text(path, limit=config.max_file_chars)
    if path.name == "wiki.md":
        if kind == "skill":
            return _summarize_skill_page(relpath, text, config)
        if kind == "agent":
            return _summarize_agent_page(relpath, text, config)
        return _summarize_text(path, relpath, text, config)
    if suffix == ".py":
        return _summarize_python(relpath, text, config)
    if suffix in {".yaml", ".yml", ".json", ".toml"}:
        return _summarize_structured(relpath, text, config)
    if suffix in {".md", ".markdown", ".txt", ".csv"}:
        return _summarize_text(path, relpath, text, config)
    return (path.stem, [f"Source file: {relpath}"], _clip(text, config.max_excerpt_chars), {})


def _summarize_skill_page(relpath: str, text: str, config: WikiConfig):
    sections = split_markdown_sections(text)
    title = extract_markdown_title(text, Path(relpath).parent.name)
    summary = [
        f"Skill page: {relpath}",
        f"Lead: {first_paragraph(text) or 'No lead paragraph.'}",
    ]
    children = [link for link in extract_markdown_links(sections.get("Child Skills", "")) if link.startswith("skill/")]
    refs = [link for link in extract_markdown_links(sections.get("Refs", "")) if link.startswith("skill/")]
    tools = extract_section_code_items(sections.get("Tools", ""))
    if children:
        summary.append("Child skills: " + ", ".join(children[:8]))
    if refs:
        summary.append("Refs: " + ", ".join(refs[:8]))
    if tools:
        summary.append("Tools: " + ", ".join(tools[:8]))
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {"tools": tools, "children": children, "refs": refs}


def _summarize_agent_page(relpath: str, text: str, config: WikiConfig):
    sections = split_markdown_sections(text)
    title = extract_markdown_title(text, Path(relpath).parent.name)
    root_skill = next((link for link in extract_markdown_links(sections.get("Root Skill", "")) if link.startswith("skill/")), "")
    tools = extract_section_code_items(sections.get("Tools", ""))
    toolboxes = extract_section_code_items(sections.get("Toolboxes", ""))
    capabilities = extract_section_code_items(sections.get("Capabilities", ""))
    summary = [f"Agent page: {title}", f"Root skill: {root_skill or 'unknown'}"]
    if tools:
        summary.append("Tools: " + ", ".join(tools[:10]))
    if toolboxes:
        summary.append("Toolboxes: " + ", ".join(toolboxes[:8]))
    if capabilities:
        summary.append("Capabilities: " + ", ".join(capabilities[:8]))
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {
        "tools": tools,
        "toolboxes": toolboxes,
        "capabilities": capabilities,
    }


def _summarize_python(relpath: str, text: str, config: WikiConfig):
    title = Path(relpath).stem.replace("_", "-")
    summary: list[str] = [f"Python module: {relpath}"]
    meta: dict[str, object] = {}
    try:
        tree = ast.parse(text)
        doc = ast.get_docstring(tree)
        if doc:
            summary.append("Docstring: " + _clip(doc.splitlines()[0].strip(), 180))
        classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        funcs = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        if classes:
            summary.append("Classes: " + ", ".join(classes[:8]))
        if funcs:
            summary.append("Functions: " + ", ".join(funcs[:8]))
        meta = {"classes": classes, "functions": funcs}
    except SyntaxError:
        summary.append("Module could not be parsed by AST; stored as plain text summary.")
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, meta


def _summarize_structured(relpath: str, text: str, config: WikiConfig):
    title = Path(relpath).stem.replace("_", "-")
    summary = [f"Structured file: {relpath}"]
    meta = {}
    try:
        if relpath.endswith((".yaml", ".yml")):
            payload = yaml.safe_load(text) or {}
        elif relpath.endswith(".json"):
            payload = json.loads(text or "{}")
        else:
            payload = {}
        if isinstance(payload, dict):
            keys = [str(key) for key in payload.keys()]
            if keys:
                summary.append("Top-level keys: " + ", ".join(keys[:10]))
            if "description" in payload:
                summary.append("Description: " + _clip(str(payload.get("description") or ""), 180))
            meta = {"keys": keys}
    except Exception:
        summary.append("Structured parse failed; stored as plain text summary.")
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, meta


def _summarize_text(path: Path, relpath: str, text: str, config: WikiConfig):
    lines = _nonempty_lines(text)
    heading = _HEADING_RE.search(text)
    bullets = [match.group(1).strip() for match in _BULLET_RE.finditer(text)]
    title = heading.group(1).strip() if heading else path.stem.replace("_", "-")
    summary = [f"Text source: {relpath}"]
    if lines:
        summary.append("Lead: " + _clip(lines[0], 180))
    for bullet in bullets[: max(0, config.max_summary_lines - len(summary))]:
        summary.append(_clip(bullet, 180))
    excerpt = _clip(text, config.max_excerpt_chars)
    return title, summary[: config.max_summary_lines], excerpt, {"line_count": len(lines)}
