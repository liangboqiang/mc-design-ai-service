from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.getenv("DESIGN_AGENTS_APP_CONFIG", str(ROOT_DIR / "config/appsetting.toml"))).resolve()


@dataclass(slots=True)
class ServerConfig:
    name: str
    host: str
    port: int
    project_root: Path
    action_base: str
    allow_publish: bool
    auto_refresh_index_on_start: bool


def load_raw() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"应用配置文件不存在：{CONFIG_PATH}")
    return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _resolve_project_root(raw_value: str | None) -> Path:
    raw = Path(os.getenv("DESIGN_AGENTS_PROJECT_ROOT", raw_value or str(ROOT_DIR)))
    return (ROOT_DIR / raw).resolve() if not raw.is_absolute() else raw.resolve()


def load_config() -> ServerConfig:
    raw = load_raw()
    server = dict(raw.get("server") or {})
    web = dict(raw.get("web") or {})
    memory = dict(raw.get("memory") or {})
    return ServerConfig(
        name=str(os.getenv("DESIGN_AGENTS_APP_NAME", server.get("name") or "mc-design-ai-service")),
        host=str(os.getenv("DESIGN_AGENTS_HOST", server.get("host") or "0.0.0.0")),
        port=int(os.getenv("DESIGN_AGENTS_PORT", server.get("port") or 18080)),
        project_root=_resolve_project_root(server.get("project_root") or "."),
        action_base=str(web.get("action_base") or "/app/action").rstrip("/"),
        allow_publish=bool(memory.get("allow_publish", False)),
        auto_refresh_index_on_start=bool(memory.get("auto_refresh_index_on_start", True)),
    )


SETTINGS = load_config()
SERVER_NAME = SETTINGS.name
SERVER_HOST = SETTINGS.host
SERVER_PORT = SETTINGS.port
PROJECT_ROOT = SETTINGS.project_root
ACTION_BASE = SETTINGS.action_base
ALLOW_PUBLISH = SETTINGS.allow_publish
AUTO_REFRESH_INDEX_ON_START = SETTINGS.auto_refresh_index_on_start
