from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from memory import MemoryService

    memory = MemoryService(AI)
    checks: dict[str, bool] = {}
    lenses = memory.list_lenses()
    checks["lenses_loaded"] = len(lenses) >= 5
    result = memory.check_note("agent.memory_native_kernel")
    checks["agent_lens_applied"] = result.get("lens", {}).get("lens_id") == "lens.agent"
    checks["runtime_ready_diagnosed"] = isinstance(result.get("diagnostics"), list) and result.get("runtime_ready") is True
    issues = [k for k, v in checks.items() if not v]
    print(f"Lens checks: {sum(checks.values())}/{len(checks)}")
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
