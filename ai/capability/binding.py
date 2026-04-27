from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class CapabilityExecutorBinder:
    """Install toolboxes and bind executor callables to CapabilitySpec.executor_ref."""

    def install_toolboxes(
        self,
        *,
        requested: list[str],
        toolbox_classes: dict[str, type[Any]],
        workspace_root: Path,
        kernel,
    ) -> dict[str, object]:  # noqa: ANN001
        installed: dict[str, object] = {}
        for name in self._ordered_unique([*requested, "engine"]):
            cls = toolbox_classes.get(name)
            if cls is None and name == "fs":
                cls = toolbox_classes.get("files")
            if cls is None:
                continue
            try:
                extension = cls().spawn(workspace_root)
            except TypeError:
                extension = cls(workspace_root=workspace_root)
            installed[getattr(extension, "toolbox_name", name)] = extension

        lookup = installed.get
        for extension in installed.values():
            bind = getattr(extension, "bind_runtime", None)
            if bind:
                try:
                    bind(kernel, lookup)
                except TypeError:
                    bind(kernel)
        return installed

    def collect_executors(self, toolbox_instances: dict[str, object]) -> dict[str, Callable[[dict], Any]]:
        executors: dict[str, Callable[[dict], Any]] = {}
        for toolbox in toolbox_instances.values():
            get_executors = getattr(toolbox, "executors", None)
            if callable(get_executors):
                for tool_id, executor in dict(get_executors()).items():
                    executors[str(tool_id)] = executor
        return executors

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
