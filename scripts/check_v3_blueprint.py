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
    main_py = read(ROOT / "__main__.py")
    checks: dict[str, bool] = {}

    checks["two_core_pages"] = "renderSearch" in app and "renderPage" in app and "renderHome" in app
    checks["page_detail_has_search"] = "topSearchInput" in app and "renderPage" in app
    checks["advanced_search_filters"] = all(x in app for x in ["entityFilter", "stageFilter", "statusFilter", "riskFilter", "onlyGovernance", "onlyDraft"])
    checks["small_status_chips"] = "statusChips" in app and ".status-chip" in css
    checks["status_to_governance_panes"] = all(x in app for x in ["renderPagePane", "update", "diagnose", "diff", "version", "risk", "draft"])
    checks["search_batch_governance"] = "renderBatchPane" in app and "wiki_batch_governance" in app
    checks["single_page_governance_integrated"] = "renderPagePane" in app and "wiki_page_update_hint" in app and "wiki_diagnose_page" in app
    checks["draft_integrated_not_center"] = "renderDraftPane" in app and "#/drafts" not in app and "草稿中心" not in app
    checks["context_pane_system"] = ".context-pane" in css and "pane-tab" in app and "pane-card" in app
    checks["graph_page_kept"] = "renderGraph" in app and "GraphAdapter" in app and "cytoscape" in app.lower()
    checks["backend_center_kept"] = "renderBackend" in app and "wiki_backend_overview" in app
    checks["user_center_kept"] = "renderUser" in app and "wiki_preview_user_folder_wikis" in app
    checks["reading_first"] = ".wiki-article" in css and ".article-surface" in css and ".reader-grid" in css and ".home-search-card" in css
    checks["status_backend"] = "def page_status_summary" in service and "wiki_page_status_summary" in actions
    checks["search_status_backend"] = "def search_with_status" in service and "wiki_search_with_status" in actions
    checks["batch_status_backend"] = "def batch_governance" in service and "wiki_batch_governance" in actions
    checks["browser_after_health"] = "_open_browser_after_ready" in main_py and "/health" in main_py
    checks["single_port_direct"] = "/app/wiki/action" in app and "mcp" not in read(ROOT / "main_app.py").lower()
    checks["old_paths_removed"] = not (AI / "mcp").exists() and not (AI / "mcp_app.py").exists() and not (AI / "config/mcpsetting.toml").exists()
    forbidden_text = ["/mcp/wiki/mcp", "/mcp/wiki/call", "__rest_tools__", "@modelcontextprotocol/sdk", "mcpClient", "wikiMcpTools", "fastmcp_compat"]
    runtime_text = "\n".join([app, service, actions, read(ROOT / "main_app.py")])
    checks["old_runtime_text_removed"] = not any(token in runtime_text for token in forbidden_text)

    issues = [k for k, v in checks.items() if not v]
    print(f"V3 blueprint match rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
