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
    r = client.get("/app/memory/actions")
    checks["memory_actions_ok"] = r.status_code == 200 and any(item.get("name") == "memory_preview_runtime" for item in r.json().get("data", []))
    r = client.post("/app/memory/action/memory_list_notes", json={"limit": 10})
    data = r.json().get("data", []) if r.status_code == 200 else []
    checks["memory_notes_listed"] = r.status_code == 200 and isinstance(data, list) and len(data) >= 2
    r = client.post("/app/memory/action/memory_compile_indexes", json={})
    indexes = r.json().get("data", {}) if r.status_code == 200 else {}
    checks["memory_indexes_compiled"] = r.status_code == 200 and "indexes" in indexes and "graph" in indexes
    issues = [k for k, v in checks.items() if not v]
    print(f"Memory checks: {sum(checks.values())}/{len(checks)}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
