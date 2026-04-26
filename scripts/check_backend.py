from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI, AI / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    checks: dict[str, bool] = {}
    checks["python_compile_ok"] = (
        compileall.compile_file(str(ROOT / "__main__.py"), quiet=1)
        and compileall.compile_file(str(ROOT / "main_app.py"), quiet=1)
        and compileall.compile_dir(str(AI), quiet=1)
    )

    from starlette.testclient import TestClient
    import main_app

    client = TestClient(main_app.app)
    r = client.get("/health")
    checks["health_ok"] = r.status_code == 200 and r.json().get("mode") == "unified-direct-functions"
    r = client.get("/app/diagnostics")
    checks["diagnostics_ok"] = r.status_code == 200 and "project_root" in r.json()
    r = client.get("/app/wiki/actions")
    checks["actions_catalog_ok"] = r.status_code == 200 and len(r.json().get("data", [])) >= 30
    r = client.post("/app/wiki/action/wiki_server_status", json={})
    checks["server_status_ok"] = r.status_code == 200 and r.json().get("ok") is True
    r = client.post("/app/wiki/action/wiki_search", json={"query": "Wiki", "limit": 2})
    checks["search_ok"] = r.status_code == 200 and r.json().get("ok") is True and isinstance(r.json().get("data"), list)
    r = client.post("/app/wiki/action/wiki_read_page", json={})
    checks["error_shape_ok"] = r.status_code in {400, 500} and r.json().get("ok") is False and "error" in r.json()

    issues = [k for k, v in checks.items() if not v]
    print(f"Backend direct-action match rate: {sum(checks.values()) / len(checks) * 100:.1f}% ({sum(checks.values())}/{len(checks)})")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
