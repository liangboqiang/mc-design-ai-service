from __future__ import annotations

from pathlib import Path


class WikiSourcePolicy:
    def include(self, project_root: Path, path: Path) -> tuple[bool, str, list[str]]:
        path = path.resolve()
        project_root = project_root.resolve()
        rel = path.relative_to(project_root).as_posix()

        if any(part in {"__pycache__", ".runtime_data", "data"} for part in path.parts):
            return False, "", []
        if path.name == "__init__.py":
            return False, "", []
        if rel.startswith("tests/"):
            return False, "", []
        if rel.endswith("/wiki.md") and rel.startswith("src/agent/"):
            return True, "agent", ["agent", "system"]
        if rel.endswith("/wiki.md") and rel.startswith("src/context/"):
            return True, "context_template", ["context", "system"]
        if rel.endswith("/wiki.md") and rel.startswith("src/tool/"):
            return True, "tool_page", ["tool", "system"]
        if rel.endswith("/wiki.md") and rel.startswith("src/skill/"):
            return True, "skill", ["skill", "system"]
        if rel.endswith("/wiki.md"):
            return True, "page", ["system"]
        if rel.startswith("src/tool/") and path.suffix in {".py", ".md", ".json", ".yaml", ".yml", ".txt"}:
            return True, "tool_source", ["tool", "system"]
        if rel.startswith("src/runtime/") and path.suffix == ".py":
            return True, "runtime_source", ["runtime", "system"]
        if rel.startswith("src/control/") and path.suffix == ".py":
            return True, "control_source", ["control", "system"]
        if rel.startswith("src/wiki/") and path.suffix == ".py":
            return True, "wiki_source", ["wiki", "system"]
        if rel.startswith("src/schemas/") and path.suffix == ".py":
            return True, "schema_source", ["schema", "system"]
        if "/knowledge/" in rel and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}:
            return True, "business_knowledge", ["business", "knowledge"]
        return False, "", []
