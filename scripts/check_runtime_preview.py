from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from workbench.preview import RuntimePreviewService
    service = RuntimePreviewService(AI)
    checks: dict[str, bool] = {}
    view = service.preview_view(task="查看当前系统运行知识视图")
    checks["preview_view_ok"] = "system_cards" in view and "business_cards" in view
    data = service.preview_runtime(task="查看当前系统运行知识视图")
    checks["preview_runtime_ok"] = isinstance(data.get("prompt"), str)
    checks["preview_runtime_has_memory_view"] = "memory_view" in data and "capability_view" in data
    issues = [k for k, v in checks.items() if not v]
    print(f"Runtime preview checks: {sum(checks.values())}/{len(checks)}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1

if __name__ == "__main__":
    import os
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
