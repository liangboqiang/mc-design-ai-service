from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WEB = ROOT / "web"
SRC = WEB / "src"
DIST = WEB / "dist"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> int:
    from scripts.build_web import build

    app = read(SRC / "assets/app.js")
    css = read(SRC / "assets/style.css")
    checks: dict[str, bool] = {}

    checks["web_src_index_exists"] = (SRC / "index.html").exists()
    checks["web_src_app_exists"] = (SRC / "assets/app.js").exists()
    checks["web_src_css_exists"] = (SRC / "assets/style.css").exists()
    checks["node_syntax_ok"] = subprocess.run(["node", "--check", str(SRC / "assets/app.js")], capture_output=True, text=True).returncode == 0
    checks["integrated_command_zone"] = "head-command" in app and "compact-command" in css and "home-browser" not in css
    checks["home_tile_portal"] = "home-tile-grid" in app and "portal-tile" in css and "home-portal-grid" not in app
    checks["home_four_tiles"] = all(x in app for x in ["历史详情页", "知识图谱", "后台中心", "用户中心"])
    checks["home_dropdown_terms"] = "renderTermDropdown" in app and "term-drop-btn" in app and "term-menu" in css
    checks["terms_under_search"] = "home-search-panel" in app and "home-dropdown-row" in app
    checks["graph_mini_tile"] = "homeGraphMini" in app and "drawHomeGraphMini" in app and "mini-svg" in css
    checks["backend_dashboard_tile"] = "dashboard-mini" in css and "全量刷新" in app
    checks["user_dialog_tile"] = "user-chat-mini" in css and "治理请求" in app
    checks["compact_fields"] = "infoIcon" in app and "info-icon" in css and "font-size: 24px" in css
    checks["search_detail_modules_kept"] = "renderSearchLoaded" in app and "renderPagePane" in app
    checks["graph_user_backend_kept"] = "renderGraph" in app and "renderBackend" in app and "renderUser" in app
    checks["no_legacy_transport"] = "/mcp/wiki/mcp" not in app and "/mcp/wiki/call" not in app and "mcpClient" not in app

    try:
        build()
        checks["python_build_ok"] = True
    except Exception as exc:
        print(f"build failed: {exc}")
        checks["python_build_ok"] = False

    html = read(DIST / "index.html") if (DIST / "index.html").exists() else ""
    checks["dist_inline_js"] = "function renderFrame" in html and "/app/wiki/action" in html
    checks["dist_inline_css"] = ".wiki-shell" in html and "Wiki App 启动失败" in html
    checks["dist_tile_portal"] = "home-tile-grid" in html and "renderTermDropdown" in html
    checks["dist_js_exists"] = (DIST / "assets/app.js").exists() and (DIST / "assets/app.js").stat().st_size > 35000
    checks["dist_css_exists"] = (DIST / "assets/style.css").exists() and (DIST / "assets/style.css").stat().st_size > 15000

    issues = [k for k, v in checks.items() if not v]
    print(f"Frontend V3.3 tile portal match rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
