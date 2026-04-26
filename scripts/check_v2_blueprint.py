from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
WEB = ROOT / "web"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    checks: dict[str, bool] = {}

    app = read(WEB / "src/assets/app.js")
    css = read(WEB / "src/assets/style.css")
    service = read(AI / "wiki_app/service.py")
    actions = read(AI / "wiki_app/actions.py")
    main_py = read(ROOT / "__main__.py")

    checks["single_repo_ai_web"] = AI.exists() and WEB.exists() and (ROOT / "__main__.py").exists()
    checks["single_port_direct_action"] = "/app/wiki/action" in app and "mcp" not in read(ROOT / "main_app.py").lower()
    checks["browser_after_health"] = "_open_browser_after_ready" in main_py and "/health" in main_py
    checks["page_update_hint_backend"] = "def page_update_hint" in service and "wiki_page_update_hint" in actions
    checks["diff_full_update_backend"] = "def update_page_diff" in service and "def update_page_full" in service
    checks["user_folder_preview_backend"] = "preview_user_folder_wikis" in service and "wiki_preview_user_folder_wikis" in actions
    checks["file_relation_workflow_ui"] = "wiki_page_file_status" in app and "wiki_update_page_diff" in app and "wiki_update_page_full" in app
    checks["graph_backend"] = "wiki_extract_knowledge_graph" in actions and "wiki_graph_neighbors" in actions and "wiki_graph_enhanced_search" in actions
    checks["graph_frontend_adapter"] = "GraphAdapter" in app and "cytoscape" in app.lower()
    checks["scope_relations_ui"] = "wiki_page_scope_relations" in app and "局部关系" in app
    checks["diagnosis_repair_ui"] = "wiki_diagnose_page" in app and "wiki_apply_diagnosis_fix" in app and "fix-action" in app
    checks["lock_disable_ui"] = "已锁定" in app and "已禁用" in app and "include_disabled" in app
    checks["wiki_like_product_ui"] = ".toc-panel" in css and ".infobox" in css and ".wiki-article" in css and "portal-grid" in css
    checks["inline_no_blank"] = "function renderShell" in read(WEB / "src/index.html") and 'src="/assets/app.js"' not in read(WEB / "src/index.html")

    forbidden_paths = [
        AI / "mcp",
        AI / "mcp_app.py",
        AI / "config/mcpsetting.toml",
    ]
    checks["old_paths_removed"] = all(not p.exists() for p in forbidden_paths)
    forbidden_text = "/mcp/wiki/mcp|/mcp/wiki/call|__rest_tools__|@modelcontextprotocol/sdk|mcpClient|wikiMcpTools|fastmcp_compat"
    checks["old_text_removed_in_runtime"] = not any(token in app or token in service or token in actions or token in read(ROOT / "main_app.py") for token in forbidden_text.split("|"))

    issues = [k for k, v in checks.items() if not v]
    print(f"V2 blueprint match rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
