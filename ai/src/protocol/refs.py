from __future__ import annotations

def resolve_refs(registry, skill_id: str) -> list[str]:  # noqa: ANN001
    return registry.base_skill_ids(skill_id)
