from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any


TOOL_PACKAGES = ("tool.external", "tool.workflow", "tool.system", "tool.wiki")


def is_toolbox_class(module_name: str, obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and obj.__module__ == module_name
        and bool(getattr(obj, "toolbox_name", ""))
        and callable(getattr(obj, "spawn", None))
    )


class ToolboxClassLoader:
    """Discover Python toolbox classes only.

    This layer intentionally does not build ToolSpec. ToolSpec belongs to
    ProtocolView compiled from Tool Wiki Pages.
    """

    def __init__(self, package_names: tuple[str, ...] = TOOL_PACKAGES):
        self.package_names = package_names

    def discover(self) -> dict[str, type[Any]]:
        classes: dict[str, type[Any]] = {}
        for module in self._iter_modules():
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if is_toolbox_class(module.__name__, obj):
                    classes[str(getattr(obj, "toolbox_name"))] = obj
        return classes

    def _iter_modules(self):
        for package_name in self.package_names:
            package = importlib.import_module(package_name)
            yield package
            if not hasattr(package, "__path__"):
                continue
            for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
                yield importlib.import_module(info.name)
