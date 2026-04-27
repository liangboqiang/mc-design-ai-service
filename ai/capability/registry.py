from __future__ import annotations

from pathlib import Path

from capability.projector import CapabilityProjector
from capability.types import CapabilitySpec
from memory import MemoryService

try:
    from protocol.registry import RuntimeRegistry
except Exception:  # noqa: BLE001
    RuntimeRegistry = None


class CapabilityRegistry:
    def __init__(self, project_root: Path, *, memory: MemoryService | None = None, legacy_registry=None):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.memory = memory or MemoryService(self.project_root)
        self.legacy_registry = legacy_registry
        self._capabilities: dict[str, CapabilitySpec] | None = None

    @classmethod
    def create(cls, project_root: Path, *, memory: MemoryService | None = None):
        legacy_registry = None
        if RuntimeRegistry is not None:
            try:
                legacy_registry = RuntimeRegistry.from_wiki(project_root)
            except Exception:  # noqa: BLE001
                legacy_registry = None
        return cls(project_root, memory=memory, legacy_registry=legacy_registry)

    def refresh(self) -> dict[str, CapabilitySpec]:
        projector = CapabilityProjector(self.project_root, self.memory)
        rows = CapabilityProjector.project_from_legacy_registry(self.legacy_registry)
        rows.update(projector.project_from_notes())
        self._capabilities = rows
        return rows

    def capabilities(self) -> dict[str, CapabilitySpec]:
        return self.refresh() if self._capabilities is None else self._capabilities

    def get(self, capability_id: str) -> CapabilitySpec | None:
        return self.capabilities().get(str(capability_id or "").strip())

    def by_kind(self, kind: str) -> list[CapabilitySpec]:
        normalized = str(kind or "").strip().lower()
        return sorted(
            [item for item in self.capabilities().values() if item.kind.lower() == normalized],
            key=lambda item: item.capability_id,
        )

    def legacy_tool_spec(self, tool_id: str):  # noqa: ANN001
        if self.legacy_registry is None:
            return None
        return self.legacy_registry.tools.get(str(tool_id or "").strip())

    def requested_tools_for_skills(self, skill_ids: list[str]) -> set[str]:
        out: set[str] = set()
        if self.legacy_registry is None:
            return out
        for skill_id in skill_ids:
            skill = self.legacy_registry.skills.get(skill_id)
            if skill is None:
                continue
            out.update(skill.tools)
        return out
