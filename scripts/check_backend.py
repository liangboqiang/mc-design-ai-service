from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def _compile_source_tree() -> bool:
    targets = [ROOT / "__main__.py", ROOT / "main_app.py", *AI.rglob("*.py")]
    for path in targets:
        if "__pycache__" in path.as_posix():
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:  # noqa: BLE001
            print(f"Compile error in {path.relative_to(ROOT)}: {exc}")
            return False
    return True


def main() -> int:
    checks: dict[str, bool] = {}
    checks["python_compile_ok"] = _compile_source_tree()
    app_js = (ROOT / "web" / "src" / "assets" / "app.js").read_text(encoding="utf-8", errors="ignore")
    api_js = (ROOT / "web" / "src" / "assets" / "api.js").read_text(encoding="utf-8", errors="ignore")
    css = (ROOT / "web" / "src" / "assets" / "style.css").read_text(encoding="utf-8", errors="ignore")
    checks["notegraf_present"] = "图谱百科" in app_js and "notebook_list" in api_js and ".应用壳" in css
    checks["atomic_transport_only"] = "/app/action/" in api_js and "/app/" + "memory/action" not in api_js + app_js and "/app/" + "workbench/action" not in api_js + app_js
    checks["removed_split_action_modules"] = not (AI / "app" / ("memory_" + "actions.py")).exists() and not (AI / "app" / ("workbench_" + "actions.py")).exists()
    checks["removed_old_core_dirs"] = not (AI / "src").exists() and not (AI / "wiki_app").exists()

    checks["app_api_source_ok"] = (ROOT / "ai" / "app" / "api.py").exists() and "/app/action/{action}" in (ROOT / "ai" / "app" / "api.py").read_text(encoding="utf-8")

    from app.actions import ActionRouter

    router = ActionRouter(ROOT)
    checks["action_catalog_ok"] = len(router.catalog()) >= 55
    notes = router.dispatch("memory_list_notes", {"limit": 3})
    checks["memory_list_notes_ok"] = isinstance(notes, list) and len(notes) >= 1
    search = router.dispatch("graphpedia_search", {"query": "", "limit": 3})
    checks["graphpedia_search_ok"] = isinstance(search, dict) and "graph" in search and "notes" in search
    notebooks = router.dispatch("notebook_list", {})
    checks["notebook_ok"] = isinstance(notebooks, dict) and "notebooks" in notebooks
    repo = router.dispatch("repo_list", {})
    checks["repo_config_ok"] = isinstance(repo, dict) and "repositories" in repo
    schemas = router.dispatch("soft_schema_list", {})
    checks["soft_schema_ok"] = isinstance(schemas, dict) and "schemas" in schemas
    roots = router.dispatch("workspace_roots", {})
    checks["workspace_roots_ok"] = isinstance(roots, dict) and "team" in roots and "user" in roots
    status = router.dispatch("version_status", {})
    checks["version_status_ok"] = isinstance(status, dict) and "dirty" in status
    gov = router.dispatch("governance_dashboard", {})
    checks["governance_dashboard_ok"] = isinstance(gov, dict) and "proposals" in gov
    issues = router.dispatch("governance_issue_list", {})
    checks["governance_issues_ok"] = isinstance(issues, dict) and "issues" in issues

    failures = [k for k, v in checks.items() if not v]
    passed = sum(checks.values())
    total = len(checks)
    lines = [f"Backend atomic-system check rate: {passed / total * 100:.1f}% ({passed}/{total})"]
    if failures:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in failures)
    os.write(1, ("\n".join(lines) + "\n").encode("utf-8"))
    os._exit(0 if not failures else 1)



if __name__ == "__main__":
    raise SystemExit(main())
