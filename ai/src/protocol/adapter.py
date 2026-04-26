from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from wiki.node import WikiNode
from .types import ProtocolDiagnostic


CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(slots=True)
class NormalizedNode:
    node: WikiNode
    node_type: str
    node_id: str
    fields: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[ProtocolDiagnostic] = field(default_factory=list)


class ProtocolAdapter:
    """Small hard adapter that compiles flexible Wiki Page semantics into fixed fields."""

    def normalize(self, node: WikiNode) -> NormalizedNode:
        node_type = self._infer_type(node)
        node_id = self._infer_id(node, node_type)
        fields: dict[str, Any] = {
            "title": node.title,
            "summary": node.summary,
            "context": self._section(node, "overview") or self._section(node, "usage") or node.summary,
            "source_node": node.node_id,
            "source_path": node.source_path,
        }
        diagnostics: list[ProtocolDiagnostic] = []

        if node_type == "agent":
            fields.update(self._agent_fields(node, diagnostics))
        elif node_type == "skill":
            fields.update(self._skill_fields(node, diagnostics))
        elif node_type == "toolbox":
            fields.update(self._toolbox_fields(node, diagnostics, node_id))
        elif node_type == "tool":
            fields.update(self._tool_fields(node, diagnostics, node_id))
        elif node_type == "service":
            pass
        else:
            node_type = "knowledge"
            fields["target_skills"] = self._runtime_list(node, "target_skills")

        return NormalizedNode(node=node, node_type=node_type, node_id=node_id, fields=fields, diagnostics=diagnostics)

    def _infer_type(self, node: WikiNode) -> str:
        runtime_type = str(node.runtime_block.get("type") or "").strip().lower()
        if runtime_type:
            return runtime_type
        if node.node_kind_hint:
            return node.node_kind_hint
        return "knowledge"

    def _infer_id(self, node: WikiNode, node_type: str) -> str:
        runtime_id = str(node.runtime_block.get("id") or "").strip()
        if runtime_id:
            return runtime_id
        if node_type == "agent":
            return node.node_id.rsplit("/", 1)[-1]
        if node_type in {"skill", "toolbox", "tool"}:
            if node_type == "tool":
                candidates = self._code_items(node, "tools")
                dotted = [item for item in candidates if "." in item and "/" not in item]
                if dotted:
                    return dotted[0]
            if node_type == "toolbox":
                candidates = self._code_items(node, "toolbox")
                if candidates:
                    return candidates[0]
            return node.node_id
        return node.node_id

    def _agent_fields(self, node: WikiNode, diagnostics: list[ProtocolDiagnostic]) -> dict[str, Any]:
        runtime = dict(node.runtime_block or {})
        root = str(runtime.get("root_skill") or "").strip()
        if not root:
            links = [*self._links(node, "root"), *self._links(node, "links")]
            root = next((link for link in links if link.startswith("skill/")), "")
        if not root:
            diagnostics.append(ProtocolDiagnostic("error", node.node_id, "Agent Wiki Page cannot infer root_skill.", "Add Root or Runtime root_skill field.", "root_skill"))
        toolboxes = self._runtime_list(node, "toolboxes") or self._code_items(node, "tools")
        reserved = {"type", "id", "root_skill", "toolboxes"}
        policy = {k: v for k, v in runtime.items() if k not in reserved}
        policy.update(self._kv_section(node, "policy"))
        return {"root_skill": root, "toolboxes": toolboxes, "policy": policy}

    def _skill_fields(self, node: WikiNode, diagnostics: list[ProtocolDiagnostic]) -> dict[str, Any]:
        child_skills = [self._link_target(link) for link in self._links(node, "children") if self._link_target(link).startswith("skill/")]
        refs = [self._link_target(link) for link in self._links(node, "links") if self._link_target(link).startswith("skill/")]
        tools = [item for item in self._code_items(node, "tools") if item and not item.startswith("tool/") and "[[" not in item]
        tools.extend(
            self._tool_id_from_link(link)
            for link in self._links(node, "tools")
            if link.startswith("tool/") or "|tool/" in link
        )
        tools = sorted(dict.fromkeys(item for item in tools if item))
        knowledge_nodes = [link for link in node.links if not link.startswith(("skill/", "tool/", "agent/"))]
        return {"child_skills": child_skills, "refs": refs, "tools": tools, "knowledge_nodes": knowledge_nodes}

    def _toolbox_fields(self, node: WikiNode, diagnostics: list[ProtocolDiagnostic], node_id: str) -> dict[str, Any]:
        module = str(node.runtime_block.get("module") or "").strip()
        class_name = str(node.runtime_block.get("class") or node.runtime_block.get("class_name") or "").strip()
        tool_ids = [
            self._tool_id_from_link(link)
            for link in self._links(node, "tools")
            if link.startswith("tool/")
        ]
        category = str(node.runtime_block.get("category") or self._infer_tool_category(node.source_path)).strip()
        return {"module": module, "class_name": class_name, "tool_ids": [item for item in tool_ids if item], "category": category}

    def _tool_fields(self, node: WikiNode, diagnostics: list[ProtocolDiagnostic], node_id: str) -> dict[str, Any]:
        input_schema = self._json_schema(node, "input")
        output_schema = self._json_schema(node, "output")
        toolbox = str(node.runtime_block.get("toolbox") or "").strip()
        if not toolbox:
            if "." in node_id:
                toolbox = node_id.split(".", 1)[0]
            else:
                toolbox = self._infer_toolbox_from_path(node.source_path)
        permission_level = self._int_from_runtime(node, "permission_level", self._default_permission(node.source_path, node_id))
        categories = self._runtime_list(node, "categories") or self._code_items(node, "category") or [self._infer_tool_category(node.source_path)]
        activation = str(node.runtime_block.get("activation") or node.runtime_block.get("activation_mode") or "").strip()
        if not activation:
            activation = "always" if any(x in node_id for x in ("read", "list", "search", "answer", "inspect")) else "skill"
        safety = self._section(node, "safety")
        if self._is_high_risk(node_id, node.source_path) and not safety:
            diagnostics.append(ProtocolDiagnostic("error", node.node_id, f"High-risk tool {node_id} is missing Safety.", "Add a Safety section.", "safety"))
        if not input_schema:
            input_schema = {"type": "object", "properties": {}}
        return {
            "toolbox": toolbox,
            "input_schema": input_schema,
            "output_schema": output_schema or {},
            "permission_level": permission_level,
            "categories": categories,
            "activation_mode": activation,
            "activation_rules": self._runtime_list(node, "activation_rules"),
            "priority": self._int_from_runtime(node, "priority", 50),
            "safety": safety,
            "context_hint": self._section(node, "usage"),
        }

    def _section(self, node: WikiNode, name: str) -> str:
        return str(node.sections.get(name) or "").strip()

    def _links(self, node: WikiNode, section: str) -> list[str]:
        return LINK_RE.findall(self._section(node, section))

    def _code_items(self, node: WikiNode, section: str) -> list[str]:
        body = self._section(node, section)
        rows = CODE_RE.findall(body)
        if rows:
            return [item.strip() for item in rows if item.strip()]
        out: list[str] = []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith("- "):
                item = s[2:].strip()
                if item.startswith("[["):
                    continue
                out.append(item.strip("`"))
        return [item for item in out if item]

    def _runtime_list(self, node: WikiNode, key: str) -> list[str]:
        value = node.runtime_block.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _kv_section(self, node: WikiNode, section: str) -> dict[str, Any]:
        body = self._section(node, section)
        data: dict[str, Any] = {}
        for line in body.splitlines():
            s = line.strip()
            if not s.startswith("- ") or ":" not in s:
                continue
            k, v = s[2:].split(":", 1)
            v = v.strip().strip("`")
            data[k.strip()] = int(v) if v.isdigit() else v
        return data

    def _json_schema(self, node: WikiNode, section: str) -> dict[str, Any]:
        body = self._section(node, section)
        match = JSON_BLOCK_RE.search(body)
        if not match:
            return {}
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return {}

    def _int_from_runtime(self, node: WikiNode, key: str, default: int) -> int:
        value = node.runtime_block.get(key)
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _link_target(link: str) -> str:
        if "|" in link:
            return link.split("|", 1)[1].strip()
        return link.strip()

    @staticmethod
    def _tool_id_from_link(link: str) -> str:
        if "|" in link:
            _, link = link.split("|", 1)
            link = link.strip()
        parts = link.split("/")
        if len(parts) >= 3 and parts[0] == "tool" and parts[1] == "wiki":
            return f"wiki_app.{parts[2]}"
        if len(parts) >= 4 and parts[0] == "tool":
            toolbox = parts[-2]
            tool_name = parts[-1]
            if toolbox == "runtime":
                toolbox = "engine"
            return f"{toolbox}.{tool_name}"
        if len(parts) >= 3:
            return ".".join(parts[1:])
        return link.replace("/", ".")

    @staticmethod
    def _infer_toolbox_from_path(path: str) -> str:
        parts = path.replace("\\\\", "/").split("/")
        if "tool" not in parts:
            return ""
        idx = parts.index("tool")
        if idx + 2 < len(parts) and parts[idx + 1] in {"external", "workflow", "system"}:
            name = parts[idx + 2]
            return "engine" if name == "runtime" else name
        return parts[idx + 1] if idx + 1 < len(parts) else ""

    @staticmethod
    def _infer_tool_category(path: str) -> str:
        parts = path.replace("\\\\", "/").split("/")
        for item in ("external", "workflow", "system"):
            if item in parts:
                return item
        return "external"

    @staticmethod
    def _default_permission(path: str, tool_id: str) -> int:
        category = ProtocolAdapter._infer_tool_category(path)
        if category == "system":
            return 3
        if category == "workflow":
            return 2
        if any(tool_id.startswith(prefix) for prefix in ("shell.", "workspace.run", "wiki_app.publish_draft")):
            return 4
        return 1

    @staticmethod
    def _is_high_risk(tool_id: str, path: str) -> bool:
        return any(tool_id.startswith(prefix) for prefix in ("shell.", "workspace.run", "wiki_app.publish_draft", "background.run"))
