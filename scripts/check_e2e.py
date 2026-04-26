from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main() -> int:
    from scripts.build_web import build
    build()

    from starlette.testclient import TestClient
    import main_app

    client = TestClient(main_app.app)
    checks: dict[str, bool] = {}

    r = client.get("/")
    html = r.text
    checks["root_html_ok"] = r.status_code == 200 and '<div id="root">' in html and "function renderFrame" in html
    checks["inline_no_external_asset_required"] = 'src="/assets/app.js"' not in html and 'href="/assets/style.css"' not in html
    checks["v33_ui_present"] = "V3.3 磁贴门户版" in html and "home-tile-grid" in html
    checks["dropdown_terms_present"] = "renderTermDropdown" in html and "term-drop-btn" in html
    checks["four_tiles_present"] = all(x in html for x in ["历史详情页", "知识图谱", "后台中心", "用户中心"])
    checks["mini_graph_present"] = "homeGraphMini" in html and "drawHomeGraphMini" in html
    checks["compact_fields_present"] = "infoIcon" in html and "info-icon" in html
    checks["search_detail_kept"] = "renderSearchLoaded" in html and "renderPagePane" in html

    js = client.get("/assets/app.js")
    checks["optional_js_asset_200"] = js.status_code == 200 and len(js.text) > 35000 and "renderHistoryTile" in js.text
    css = client.get("/assets/style.css")
    checks["optional_css_asset_200"] = css.status_code == 200 and len(css.text) > 15000 and ".portal-tile" in css.text

    r = client.get("/health")
    checks["health_200"] = r.status_code == 200 and r.json().get("status") == "ok"
    r = client.post("/app/wiki/action/wiki_extract_knowledge_graph", json={"include_graph": True, "write_store": True})
    checks["graph_action_not_500"] = r.status_code == 200 and r.json().get("ok") is True
    r = client.post("/app/wiki/action/wiki_search_with_status", json={"query": "", "limit": 3})
    checks["search_with_status_action_ok"] = r.status_code == 200 and r.json().get("ok") is True and isinstance(r.json().get("data", {}).get("results"), list)
    r = client.post("/app/wiki/action/wiki_user_file_tree", json={"relative_path": ""})
    checks["user_file_tree_action_ok"] = r.status_code == 200 and r.json().get("ok") is True and "items" in r.json().get("data", {})
    r = client.get("/some/spa/route")
    checks["spa_fallback_ok"] = r.status_code == 200 and "function renderFrame" in r.text

    issues = [k for k, v in checks.items() if not v]
    print(f"E2E V3.3 closed-loop rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
