from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ActionResponse:
    ok: bool
    action: str
    data: Any = None
    error: dict | None = None
