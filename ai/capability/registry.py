from __future__ import annotations

from pathlib import Path

from capability.projector import CapabilityProjector
from capability.types import CapabilitySpec
from memory import MemoryService


class CapabilityRegistry:
    """Memory-native capability catalog.

    The registry projects CapabilitySpec directly from note.md. It does not import or
    depend on the removed protocol/runtime transition layers.
    """

    def __init__(self, project_root: Path, *, memory: MemoryService | None = None):
        self.project_root = Path(project_root).resolve()
        self.memory = memory or MemoryService(self.project_root)
        self._capabilities: dict[str, CapabilitySpec] | None = None

    @classmethod
    def create(cls, project_root: Path, *, memory: MemoryService | None = None, **_: object):
        return cls(project_root, memory=memory)

    def refresh(self) -> dict[str, CapabilitySpec]:
        self._capabilities = CapabilityProjector(self.project_root, self.memory).project_from_notes()
        return self._capabilities

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

    def requested_tools_for_skills(self, skill_ids: list[str]) -> set[str]:
        out: set[str] = set()
        capabilities = self.capabilities()
        for skill_id in skill_ids:
            skill = capabilities.get(skill_id)
            if skill is None:
                continue
            for target in skill.metadata.get("links", []) + skill.metadata.get("relations", []):
                tool_id = _tool_id_from_ref(target)
                if tool_id and tool_id in capabilities:
                    out.add(tool_id)
        return out


def _tool_id_from_ref(ref: str) -> str:
    raw = str(ref or "").strip()
    if raw.startswith("tool/"):
        parts = raw.split("/")
        if len(parts) >= 4:
            toolbox = "engine" if parts[-2] == "runtime" else parts[-2]
            return f"{toolbox}.{parts[-1]}"
    return raw if "." in raw and "/" not in raw else ""
