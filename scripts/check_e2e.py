from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from scripts.build_web import build
    build()
    html = (ROOT / "web/dist/index.html").read_text(encoding="utf-8")
    app = (ROOT / "web/dist/assets/app.js").read_text(encoding="utf-8")
    checks = {
        "root_html_ok": '<div id="root">' in html,
        "inline_no_external_asset_required": 'src="/assets/app.js"' not in html and 'href="/assets/style.css"' not in html,
        "notegraf_ui_present": "NoteGraph" in html and "图谱百科" in html and "记事本" in html,
        "atomic_action_transport": "/app/action/" in html and "/app/" + "memory/action" not in html and "/app/" + "workbench/action" not in html,
        "note_actions_present": "memory_read_note_detail" in app and "memory_graph_view" in app,
    }
    issues = [k for k, v in checks.items() if not v]
    print(f"E2E atomic NoteGraph closed-loop rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    main()
