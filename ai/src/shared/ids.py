from __future__ import annotations

import uuid


def new_id(prefix: str, *, length: int = 8) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:length]}"
