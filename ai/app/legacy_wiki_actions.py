from __future__ import annotations

from pathlib import Path
from typing import Any

from wiki_app.actions import WikiAppActionRouter, action_catalog as legacy_catalog


class LegacyWikiActionRouter:
    def __init__(self, project_root: Path | None = None, allow_publish: bool | None = None):
        self.router = WikiAppActionRouter(project_root=project_root, allow_publish=allow_publish)

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        return self.router.dispatch(action, payload)

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        return legacy_catalog()
