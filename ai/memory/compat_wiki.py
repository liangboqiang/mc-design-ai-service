from __future__ import annotations

from pathlib import Path
from typing import Any

from memory import MemoryService


class RuntimeMemoryBridge:
    """Compatibility bridge so runtime can speak Memory without importing WikiHub."""

    def __init__(self, project_root: Path, *, session=None):  # noqa: ANN001
        self.service = MemoryService(project_root, session=session)

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        return self.service.ingest(files)

    def state_fragments(self) -> list[str]:
        return self.service.state_fragments()

    def system_brief(self) -> str:
        return self.service.summary()

    def orient(self, observation: Any, *, runtime_state=None):  # noqa: ANN001
        return self.service.orient(observation, runtime_state=runtime_state)

    def capture(self, step: Any):  # noqa: ANN001
        return self.service.capture(step)
