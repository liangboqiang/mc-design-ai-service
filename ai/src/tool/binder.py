from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from protocol.types import ToolSpec


class ToolExecutorBinder:
    """Bind ToolSpec metadata from Wiki to Python executors from toolbox classes."""

    def install_toolboxes(
        self,
        *,
        requested: list[str],
        toolbox_classes: dict[str, type[Any]],
        workspace_root: Path,
        runtime,
    ) -> dict[str, object]:
        installed: dict[str, object] = {}
        for name in self._ordered_unique([*requested, "engine"]):
            cls = toolbox_classes.get(name)
            if cls is None:
                continue
            extension = cls().spawn(workspace_root)
            installed[getattr(extension, "toolbox_name", name)] = extension

        lookup = installed.get
        for extension in installed.values():
            bind = getattr(extension, "bind_runtime", None)
            if bind:
                try:
                    bind(runtime, lookup)
                except TypeError:
                    bind(runtime)
        return installed

    def bind(self, specs: dict[str, ToolSpec], toolbox_instances: dict[str, object]) -> dict[str, ToolSpec]:
        executors: dict[str, object] = {}
        for toolbox in toolbox_instances.values():
            get_executors = getattr(toolbox, "executors", None)
            if callable(get_executors):
                for tool_id, executor in dict(get_executors()).items():
                    executors[str(tool_id)] = executor

        bound: dict[str, ToolSpec] = {}
        for tool_id, executor in executors.items():
            if tool_id not in specs:
                continue
            bound[tool_id] = replace(specs[tool_id], executor=executor)
        return bound

    @staticmethod
    def _ordered_unique(rows: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in rows:
            normalized = str(item).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                out.append(normalized)
        return out
