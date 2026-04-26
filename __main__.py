from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys
import threading
import time
import urllib.request
import webbrowser

ROOT_DIR = Path(__file__).resolve().parent
AI_DIR = ROOT_DIR / "ai"
AI_SRC_DIR = AI_DIR / "src"
WEB_DIR = ROOT_DIR / "web"
WEB_DIST_DIR = WEB_DIR / "dist"
BUILD_STAMP = WEB_DIST_DIR / ".wiki_app_build.json"

for candidate in (ROOT_DIR, AI_DIR, AI_SRC_DIR):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)

import uvicorn  # noqa: E402
import config_loader as cfg  # noqa: E402
from scripts.build_web import source_hash, build as build_web  # noqa: E402


def _dist_is_current() -> bool:
    index = WEB_DIST_DIR / "index.html"
    if not index.exists() or not BUILD_STAMP.exists():
        return False
    try:
        stamp = json.loads(BUILD_STAMP.read_text(encoding="utf-8"))
    except Exception:
        return False
    return stamp.get("source_hash") == source_hash()


def ensure_web_build(force: bool = False) -> None:
    if _dist_is_current() and not force:
        print("[web] dist is current; skip rebuild.")
        return
    print("[web] building web/dist with Python builder...")
    build_web()
    if not (WEB_DIST_DIR / "index.html").exists():
        raise SystemExit("前端构建失败：web/dist/index.html 不存在。")


def run_checks() -> None:
    from scripts import check_backend, check_frontend, check_e2e, check_v33_blueprint, check_cleanup_and_closure

    for name, module in [
        ("backend", check_backend),
        ("frontend", check_frontend),
        ("e2e", check_e2e),
        ("blueprint", check_v33_blueprint),
        ("cleanup", check_cleanup_and_closure),
    ]:
        print(f"[check] {name}")
        code = module.main()
        if code != 0:
            raise SystemExit(code)



def _open_browser_after_ready(port: int) -> None:
    def worker() -> None:
        health = f"http://127.0.0.1:{port}/health"
        target = f"http://127.0.0.1:{port}/"
        for _ in range(80):
            try:
                with urllib.request.urlopen(health, timeout=0.35) as response:
                    if response.status == 200:
                        webbrowser.open(target)
                        return
            except Exception:
                time.sleep(0.15)
        try:
            webbrowser.open(target)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()


def print_banner() -> None:
    print("\n" + "=" * 78)
    print("  MC Design AI Service - Unified Direct Wiki App")
    print(f"  URL:        http://127.0.0.1:{cfg.SERVER_PORT}/")
    print("  Mode:       direct internal functions")
    print(f"  Project:    {cfg.PROJECT_ROOT}")
    print(f"  Web dist:   {WEB_DIST_DIR}")
    print("  Transport:  browser -> /app/wiki/action/* -> WikiHub/WikiWorkbench")
    print("=" * 78 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start MC Design AI Service unified Wiki app.")
    parser.add_argument("--build-web", action="store_true", help="Build web if missing or stale.")
    parser.add_argument("--rebuild-web", action="store_true", help="Force rebuild web before starting.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically.")
    parser.add_argument("--check", action="store_true", help="Run backend/frontend/e2e checks and exit.")
    args = parser.parse_args()

    if args.check:
        run_checks()
        return

    ensure_web_build(force=args.rebuild_web or args.build_web)
    print_banner()

    if not args.no_browser:
        _open_browser_after_ready(cfg.SERVER_PORT)

    uvicorn.run(
        "main_app:app",
        host=cfg.SERVER_HOST,
        port=cfg.SERVER_PORT,
        reload=False,
        lifespan="on",
    )


if __name__ == "__main__":
    main()
