from __future__ import annotations

from pathlib import Path

import config_loader as cfg
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.actions import ActionRouter
from app.diagnostics import collect_diagnostics


class AppRuntime:
    def __init__(self):
        self.actions = ActionRouter()


def create_app(*, root_dir: Path, ai_dir: Path, web_dir: Path, web_dist_dir: Path) -> Starlette:
    runtime = AppRuntime()

    def _index_path() -> Path:
        return web_dist_dir / "index.html"

    def _diagnostic_html(title: str, message: str) -> HTMLResponse:
        return HTMLResponse(
            f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>{title}</title><style>
            body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,sans-serif; background:#f8fafc; color:#0f172a; }}
            main {{ max-width:860px; margin:10vh auto; background:white; border:1px solid #e2e8f0; border-radius:24px; padding:32px; box-shadow:0 20px 60px rgba(15,23,42,.08); }}
            pre {{ background:#0f172a; color:#e2e8f0; padding:16px; border-radius:16px; overflow:auto; }}
            </style></head><body><main><h1>{title}</h1><p>{message}</p><pre>python __main__.py --rebuild-web</pre></main></body></html>""",
            status_code=200,
        )

    async def health(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "server": cfg.SERVER_NAME,
                "port": cfg.SERVER_PORT,
                "mode": "memory-native-agent-kernel",
                "transport": "atomic-actions",
                "project_root": str(cfg.PROJECT_ROOT),
            }
        )

    async def app_config(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "actionBase": "/app/action",
                "mode": "same-origin-atomic-actions",
                "serverPort": cfg.SERVER_PORT,
            }
        )

    async def app_diagnostics(request: Request) -> JSONResponse:
        return JSONResponse(collect_diagnostics(root_dir, ai_dir, web_dir, cfg.PROJECT_ROOT))

    async def list_actions(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True, "data": runtime.actions.catalog()})

    async def app_action(request: Request) -> JSONResponse:
        return await _dispatch(runtime.actions, "app", request)

    async def spa_index(request: Request) -> Response:
        index = _index_path()
        if not index.exists():
            return _diagnostic_html("Memory-Native Workbench 前端尚未构建", "当前 AI 后端已经启动，但 web/dist/index.html 不存在。")
        return FileResponse(index, headers={"Cache-Control": "no-store, max-age=0"})

    async def web_fallback(request: Request) -> Response:
        rel_path = request.path_params.get("path", "")
        target = (web_dist_dir / rel_path).resolve()
        dist_root = web_dist_dir.resolve()
        if dist_root in [target, *target.parents] and target.is_file():
            return FileResponse(target, headers={"Cache-Control": "no-store, max-age=0"})
        return await spa_index(request)

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/app-config.json", app_config, methods=["GET"]),
            Route("/app/diagnostics", app_diagnostics, methods=["GET"]),
            Route("/app/actions", list_actions, methods=["GET"]),
            Route("/app/action/{action}", app_action, methods=["POST"]),
            Mount("/assets", StaticFiles(directory=web_dist_dir / "assets", check_dir=False), name="assets"),
            Route("/", spa_index, methods=["GET"]),
            Route("/{path:path}", web_fallback, methods=["GET"]),
        ]
    )


async def _dispatch(router, namespace: str, request: Request) -> JSONResponse:  # noqa: ANN001
    action = request.path_params["action"]
    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}
    try:
        data = router.dispatch(action, payload)
        return JSONResponse({"ok": True, "namespace": namespace, "action": action, "data": data})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            {
                "ok": False,
                "namespace": namespace,
                "action": action,
                "error": {"code": "ACTION_ERROR", "message": str(exc), "type": type(exc).__name__},
            },
            status_code=400 if isinstance(exc, (ValueError, FileNotFoundError, KeyError)) else 500,
        )
