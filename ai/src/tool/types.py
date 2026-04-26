from __future__ import annotations

from collections.abc import Callable
from typing import Any

ToolExecutor = Callable[[dict[str, Any]], str]
