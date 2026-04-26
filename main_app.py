from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent
AI_DIR = ROOT_DIR / "ai"
AI_SRC_DIR = AI_DIR / "src"
WEB_DIR = ROOT_DIR / "web"
WEB_DIST_DIR = WEB_DIR / "dist"

for candidate in (ROOT_DIR, AI_DIR, AI_SRC_DIR):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)

import config_loader as cfg  # noqa: E402
from wiki_app.actions import WikiAppActionRouter, action_catalog, error_response  # noqa: E402
from wiki_app.diagnostics import collect_diagnostics  # noqa: E402


router = WikiAppActionRouter()


def _index_path() -> Path:
    return WEB_DIST_DIR / "index.html"


def _diagnostic_html(title: str, message: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{title}</title>
          <style>
            body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,sans-serif; background:#f8fafc; color:#0f172a; }}
            main {{ max-width:860px; margin:10vh auto; background:white; border:1px solid #e2e8f0; border-radius:24px; padding:32px; box-shadow:0 20px 60px rgba(15,23,42,.08); }}
            code {{ background:#f1f5f9; padding:2px 6px; border-radius:6px; }}
            pre {{ background:#0f172a; color:#e2e8f0; padding:16px; border-radius:16px; overflow:auto; }}
          </style>
        </head>
        <body><main><h1>{title}</h1><p>{message}</p><pre>python __main__.py --rebuild-web</pre></main></body></html>""",
        status_code=200,
    )


async def health(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": cfg.SERVER_NAME,
            "port": cfg.SERVER_PORT,
            "mode": "unified-direct-functions",
            "project_root": str(cfg.PROJECT_ROOT),
        }
    )


async def app_config(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "wikiActionBase": cfg.ACTION_BASE,
            "mode": "same-origin-direct-functions",
            "serverPort": cfg.SERVER_PORT,
        }
    )


async def app_diagnostics(request: Request) -> JSONResponse:
    return JSONResponse(collect_diagnostics(ROOT_DIR, AI_DIR, WEB_DIR, cfg.PROJECT_ROOT))


async def list_actions(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "data": action_catalog()})


async def wiki_action(request: Request) -> JSONResponse:
    action = request.path_params["action"]
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}
    try:
        data = router.dispatch(action, payload)
        return JSONResponse({"ok": True, "action": action, "data": data})
    except Exception as exc:
        status_code, body = error_response(action, exc)
        return JSONResponse(body, status_code=status_code)


async def spa_index(request: Request) -> Response:
    index = _index_path()
    if not index.exists():
        return _diagnostic_html("Wiki App 前端尚未构建", "当前 AI 后端已经启动，但 web/dist/index.html 不存在。")
    return FileResponse(index, headers={"Cache-Control": "no-store, max-age=0"})


async def web_fallback(request: Request) -> Response:
    rel_path = request.path_params.get("path", "")
    target = (WEB_DIST_DIR / rel_path).resolve()
    dist_root = WEB_DIST_DIR.resolve()
    if dist_root in [target, *target.parents] and target.is_file():
        return FileResponse(target, headers={"Cache-Control": "no-store, max-age=0"})
    return await spa_index(request)


def create_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/app-config.json", app_config, methods=["GET"]),
            Route("/app/diagnostics", app_diagnostics, methods=["GET"]),
            Route("/app/wiki/actions", list_actions, methods=["GET"]),
            Route("/app/wiki/action/{action}", wiki_action, methods=["POST"]),
            Mount("/assets", StaticFiles(directory=WEB_DIST_DIR / "assets", check_dir=False), name="assets"),
            Route("/", spa_index, methods=["GET"]),
            Route("/{path:path}", web_fallback, methods=["GET"]),
        ]
    )


app = create_app()
