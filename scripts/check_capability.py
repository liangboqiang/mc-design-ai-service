from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from capability import CapabilityRegistry
    from workbench.preview import RuntimePreviewService

    registry = CapabilityRegistry.create(AI)
    preview = RuntimePreviewService(AI).preview_runtime(task="请预览当前智能体运行时")
    checks: dict[str, bool] = {}
    checks["capabilities_loaded"] = len(registry.capabilities()) > 0
    checks["tools_projected"] = any(item.kind == "Tool" for item in registry.capabilities().values())
    checks["preview_has_capability_view"] = isinstance(preview.get("capability_view"), dict)
    checks["visible_tools_field_present"] = "visible_tools" in preview.get("capability_view", {})
    issues = [k for k, v in checks.items() if not v]
    print(f"Capability checks: {sum(checks.values())}/{len(checks)}")
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
