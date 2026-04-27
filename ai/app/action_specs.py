from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionSpec:
    name: str
    method: str
    required: tuple[str, ...] = ()
    defaults: dict[str, Any] = field(default_factory=dict)
    description: str = ""


def build_params(spec: ActionSpec, payload: dict[str, Any]) -> dict[str, Any]:
    params = dict(spec.defaults)
    params.update(payload)
    for name in spec.required:
        if not str(params.get(name, "")).strip():
            raise ValueError(f"缺少必要参数：{name}")
    return params


def action_catalog(actions: dict[str, ActionSpec]) -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "method": spec.method,
            "required": list(spec.required),
            "defaults": spec.defaults,
            "description": spec.description,
        }
        for spec in actions.values()
    ]
