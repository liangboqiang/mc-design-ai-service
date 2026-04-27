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
    api = read(SRC / "assets/api.js")
    checks: dict[str, bool] = {}

    checks["web_src_index_exists"] = (SRC / "index.html").exists()
    checks["web_src_app_exists"] = (SRC / "assets/app.js").exists()
    checks["web_src_css_exists"] = (SRC / "assets/style.css").exists()
    checks["node_syntax_ok"] = subprocess.run(["node", "--check", str(SRC / "assets/app.js")], capture_output=True, text=True).returncode == 0
    checks["atomic_api_client"] = "/app/action/" in api and "/app/" + "memory/action" not in api and "/app/" + "workbench/action" not in api
    checks["notegraf_routes"] = "#/repo" in app and "#/governance" in app and "#/note" in app
    checks["actions_used"] = "graphpedia_search" in api and "notebook_list" in api and "governance_issue_list" in api
    checks["chinese_first_ui"] = "图谱百科" in app and "记事本" in app and "审核治理" in app and "笔记详情" in app
    checks["compact_layout_present"] = "应用壳" in app and ".侧栏" in css and "开源图谱画布" in css
    checks["old_repo_page_removed"] = "渲染仓库配置" not in app and "新建仓库" not in app
    checks["graph_component_present"] = "NoteGraphForce" in read(SRC / "assets/graphin_offline.js")

    try:
        build()
        checks["python_build_ok"] = True
    except Exception as exc:
        print(f"build failed: {exc}")
        checks["python_build_ok"] = False

    html = read(DIST / "index.html") if (DIST / "index.html").exists() else ""
    checks["dist_inline_js"] = "图谱百科" in html and "graphpedia_search" in html and "/app/action/" in html
    checks["dist_no_old_transport"] = "/app/" + "memory/action" not in html and "/app/" + "workbench/action" not in html and "/app/" + "wiki/action" not in html
    checks["dist_inline_css"] = ".应用壳" in html and "开源图谱画布" in html
    checks["dist_js_exists"] = (DIST / "assets/app.js").exists() and (DIST / "assets/app.js").stat().st_size > 10000
    checks["dist_css_exists"] = (DIST / "assets/style.css").exists() and (DIST / "assets/style.css").stat().st_size > 5000

    issues = [k for k, v in checks.items() if not v]
    print(f"Frontend atomic NoteGraph match rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
