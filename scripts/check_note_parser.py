from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI, AI / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def main() -> int:
    from memory.store import NoteStore

    store = NoteStore(AI)
    notes = store.notes()
    checks: dict[str, bool] = {}
    checks["note_md_loaded"] = "agent.memory_native_kernel" in notes
    checks["wiki_md_compatible"] = any(note.path.endswith("wiki.md") for note in notes.values())
    agent = notes.get("agent.memory_native_kernel")
    checks["frontmatter_parsed"] = agent is not None and agent.kind == "Agent" and agent.lens_id == "lens.agent"
    checks["relations_parsed"] = agent is not None and any(rel.predicate == "uses" for rel in agent.relations)
    issues = [k for k, v in checks.items() if not v]
    print(f"Note parser checks: {sum(checks.values())}/{len(checks)}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
