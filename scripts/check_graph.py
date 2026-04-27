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

    graph = MemoryService(AI).graph({"write_store": False, "include_hidden": True})
    checks: dict[str, bool] = {}
    checks["graph_has_nodes"] = graph.get("node_count", 0) > 0
    checks["graph_has_edges"] = isinstance(graph.get("edges"), list)
    checks["edges_have_metadata"] = all(all(key in edge for key in ["kind", "status", "evidence"]) for edge in graph.get("edges", [])[:20])
    checks["no_entity_type_triples"] = all(triple.get("predicate") not in {"实体类型", "作用范围"} for triple in graph.get("triples", []))
    issues = [k for k, v in checks.items() if not v]
    print(f"Graph checks: {sum(checks.values())}/{len(checks)}")
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
