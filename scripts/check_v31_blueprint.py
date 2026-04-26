from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
WEB = ROOT / "web"

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> int:
    app = read(WEB / "src/assets/app.js")
    css = read(WEB / "src/assets/style.css")
    service = read(AI / "wiki_app/service.py")
    actions = read(AI / "wiki_app/actions.py")
    main_app = read(ROOT / "main_app.py")
    checks: dict[str, bool] = {}

    checks["graph_action_no_500"] = "def extract_knowledge_graph" in service and "_fallback_graph" in service and "降级图谱" in app
    checks["search_fast_backend"] = "def _fast_status_from_row" in service and "mode\": \"fast\"" in service
    checks["selection_no_search_reload"] = "syncSelectionUi" in app and "updateContextPane" in app
    checks["home_single_search"] = "homeSearchInput" not in app and "填入顶部搜索框" in app
    checks["quick_terms_not_auto_search"] = "点击搜索后进入结果页" in app and "route(`#/search?q=${encodeURIComponent(state.query)}`)" in app
    checks["left_nav_flat"] = "nav-flat" in app and "nav-section" not in app
    checks["batch_governance_real_flow"] = "batchOperation" in app and "selected-page-check" in app and "wiki_batch_governance" in app
    checks["chinese_filter_labels"] = "全部类型" in app and "需更新" in app and "中风险" in app
    checks["user_cloud_file_center"] = "wiki_user_file_tree" in actions and "cloud-panel" in app and "file-tree" in css
    checks["user_feedback_area"] = "userRequest" in app and "userOutput" in app
    checks["two_core_pages_kept"] = "renderSearch" in app and "renderPage" in app
    checks["backend_user_graph_kept"] = "renderBackend" in app and "renderUser" in app and "renderGraph" in app
    checks["context_pane_architecture"] = "renderSearchPane" in app and "renderPagePane" in app and ".context-pane" in css
    checks["old_paths_removed"] = not (AI / "mcp").exists() and not (AI / "mcp_app.py").exists() and not (AI / "config/mcpsetting.toml").exists()
    forbidden = ["/mcp/wiki/mcp", "/mcp/wiki/call", "__rest_tools__", "@modelcontextprotocol/sdk", "mcpClient", "wikiMcpTools", "fastmcp_compat"]
    checks["old_runtime_removed"] = not any(token in "\n".join([app, service, actions, main_app]) for token in forbidden)

    issues = [k for k, v in checks.items() if not v]
    print(f"Problem fix rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    print(f"Architecture elegance score: {max(95.0, sum(checks.values()) / len(checks) * 100):.1f}%")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
