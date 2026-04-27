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
    notes = memory.list_notes(limit=10)
    checks["memory_notes_listed"] = isinstance(notes, list) and len(notes) >= 2
    indexes = memory.compile_indexes()
    checks["memory_indexes_compiled"] = "indexes" in indexes and "graph" in indexes
    preview = memory.orient("检查 MemoryView")
    checks["memory_orient_ok"] = bool(getattr(preview, "task_brief", ""))
    issues = [k for k, v in checks.items() if not v]
    print(f"Memory checks: {sum(checks.values())}/{len(checks)}")
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
