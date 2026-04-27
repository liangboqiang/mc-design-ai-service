from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI, AI / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from starlette.testclient import TestClient
    import main_app

    client = TestClient(main_app.app)
    checks: dict[str, bool] = {}
    r = client.post("/app/memory/action/memory_preview_view", json={"task": "查看当前系统运行知识视图"})
    view = r.json().get("data", {}) if r.status_code == 200 else {}
    checks["preview_view_ok"] = r.status_code == 200 and "system_cards" in view and "business_cards" in view
    r = client.post("/app/memory/action/memory_preview_runtime", json={"task": "查看当前系统运行知识视图"})
    data = r.json().get("data", {}) if r.status_code == 200 else {}
    checks["preview_runtime_ok"] = r.status_code == 200 and isinstance(data.get("prompt"), str)
    checks["preview_runtime_has_memory_view"] = "memory_view" in data and "capability_view" in data
    issues = [k for k, v in checks.items() if not v]
    print(f"Runtime preview checks: {sum(checks.values())}/{len(checks)}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
