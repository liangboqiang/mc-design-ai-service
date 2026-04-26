from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
WEB = ROOT / "web"

def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> int:
    cleanup_checks: dict[str, bool] = {}
    closure_checks: dict[str, bool] = {}

    removed_paths = [
        AI / "mcp",
        AI / "mcp_app.py",
        AI / "config/mcpsetting.toml",
        ROOT / "UNIFIED_AI_WEB_DELIVERY_REPORT.txt",
        ROOT / "DIRECT_FUNCTION_UNIFIED_DELIVERY_REPORT.txt",
        ROOT / "FRONTEND_BUILD_FIX_REPORT.txt",
        ROOT / "BLANK_PAGE_FIX_REPORT.txt",
        ROOT / "DELIVERY_REPORT.md",
        ROOT / "INLINE_FRONTEND_FIX_REPORT.md",
        ROOT / "WIKI_WORKBENCH_V2_PRODUCTIZED_REPORT.md",
        ROOT / "WIKI_WORKBENCH_V3_CONTEXT_PANES_REPORT.md",
        ROOT / "WIKI_WORKBENCH_V31_POLISHED_REPORT.md",
        ROOT / "WIKI_WORKBENCH_V32_HOME_REDESIGN_REPORT.md",
    ]
    for path in removed_paths:
        cleanup_checks[f"removed:{path.relative_to(ROOT)}"] = not path.exists()

    app = text(WEB / "src/assets/app.js")
    css = text(WEB / "src/assets/style.css")
    service = text(AI / "wiki_app/service.py")
    actions = text(AI / "wiki_app/actions.py")
    runtime = "\n".join([app, css, service, actions, text(ROOT / "main_app.py")])
    for token in ["/mcp/wiki/mcp", "/mcp/wiki/call", "__rest_tools__", "@modelcontextprotocol/sdk", "fastmcp_compat", "mcpClient", "wikiMcpTools"]:
        cleanup_checks[f"runtime_no:{token}"] = token not in runtime

    closure_checks["startup_health_fixed"] = "_open_browser_after_ready" in text(ROOT / "__main__.py")
    closure_checks["tile_home_closed"] = "home-tile-grid" in app and "portal-tile" in css
    closure_checks["dropdown_terms_closed"] = "renderTermDropdown" in app and "term-menu.open" in css
    closure_checks["four_tiles_closed"] = all(x in app for x in ["renderHistoryTile", "renderGraphTile", "renderBackendTile", "renderUserTile"])
    closure_checks["compact_fields_closed"] = "infoIcon" in app and "info-icon" in css
    closure_checks["search_closed"] = "renderSearch" in app and "wiki_search_with_status" in app
    closure_checks["page_detail_closed"] = "renderPage" in app and "renderPagePane" in app
    closure_checks["graph_closed"] = "_fallback_graph" in service and "renderGraph" in app
    closure_checks["user_center_closed"] = "wiki_user_file_tree" in actions and "renderUser" in app

    clean_passed = sum(cleanup_checks.values())
    clean_total = len(cleanup_checks)
    closure_passed = sum(closure_checks.values())
    closure_total = len(closure_checks)
    print(f"Old redundancy cleanup rate: {clean_passed / clean_total * 100:.1f}% ({clean_passed}/{clean_total})")
    print(f"Functional closed-loop rate: {closure_passed / closure_total * 100:.1f}% ({closure_passed}/{closure_total})")
    issues = [k for k, v in cleanup_checks.items() if not v] + [k for k, v in closure_checks.items() if not v]
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
