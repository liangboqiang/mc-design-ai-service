from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any
from workspace_paths import workspace_root

ADAPTER_PACKAGE_ROOTS = (
    ("capability.adapters.external", "external"),
    ("capability.adapters.workflow", "workflow"),
    ("capability.adapters.system", "system"),
)


def is_toolbox_class(module_name: str, obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and obj.__module__ == module_name
        and bool(getattr(obj, "toolbox_name", ""))
        and callable(getattr(obj, "spawn", None))
    )


class CapabilityClassLoader:
    """Discover Python toolbox classes for Capability executors.

    Phase 7 removes the legacy source tree. Toolbox code now lives under ai/capability/adapters
    and note.md lives under data/notes/system/tool.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.adapter_root = workspace_root(self.project_root) / "ai" / "capability" / "adapters"

    def discover(self) -> dict[str, type[Any]]:
        classes: dict[str, type[Any]] = {}
        for package_name, rel_dir in ADAPTER_PACKAGE_ROOTS:
            root = self.adapter_root / rel_dir
            if not root.exists():
                continue
            for path in sorted(root.rglob("toolbox.py")):
                rel = path.relative_to(root).with_suffix("")
                module_name = package_name + "." + ".".join(rel.parts)
                try:
                    module = importlib.import_module(module_name)
                except Exception:
                    continue
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if is_toolbox_class(module.__name__, obj):
                        classes[str(getattr(obj, "toolbox_name"))] = obj
        return classes
