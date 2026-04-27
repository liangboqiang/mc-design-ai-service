from __future__ import annotations
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
WEB = ROOT / "web"

FORBIDDEN_PATHS = [
    AI / "wiki_app",
    AI / "src",
    AI / "src" / "wiki",
    AI / "src" / "protocol",
    AI / "src" / "runtime",
    AI / "app" / "legacy_wiki_actions.py",
    AI / "app" / ("memory_" + "actions.py"),
    AI / "app" / ("workbench_" + "actions.py"),
    AI / "memory" / "compat_wiki.py",
    AI / "memory" / "runtime_bridge.py",
    AI / "src" / "tool" / "binder.py",
    AI / "src" / "tool" / "loader.py",
]
FORBIDDEN_TEXT = [
    "/app/" + "wiki/action",
    "/app/" + "memory/action",
    "/app/" + "workbench/action",
    "wiki" + "ActionBase",
    "Wiki" + "AppService",
    "Wiki" + "AppActionRouter",
    "Wiki" + "Hub",
    "Wiki" + "Workbench",
    "Protocol" + "Compiler",
    "Protocol" + "View",
    "Runtime" + "Registry",
    "Runtime" + "Kernel",
    "Turn" + "Loop",
    "Tool" + "Surface",
    "Tool" + "Spec",
    "Agent" + "Spec",
    "Skill" + "Spec",
]


def iter_text_files():
    bases = [AI, WEB / "src", ROOT / "main_app.py", ROOT / "__main__.py", ROOT / "scripts"]
    for base in bases:
        if base.is_file():
            yield base
            continue
        for path in base.rglob("*"):
            rel = path.relative_to(ROOT).as_posix()
            if "__pycache__" in rel or rel.startswith("web/dist/"):
                continue
            if path.is_file() and path.suffix in {".py", ".js", ".html", ".md", ".json", ".toml", ".yaml", ".yml"}:
                yield path


def main() -> int:
    checks: dict[str, bool] = {}
    for path in FORBIDDEN_PATHS:
        checks[f"removed:{path.relative_to(ROOT)}"] = not path.exists()
    offenders: list[str] = []
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in FORBIDDEN_TEXT:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {token}")
                break
    checks["no_forbidden_legacy_text"] = not offenders
    checks["no_non_note_md_files"] = not any(ROOT.rglob("wiki" + ".md"))
    passed = sum(checks.values())
    total = len(checks)
    print(f"No-legacy-core checks: {passed}/{total}")
    if offenders:
        print("Legacy text offenders:")
        for item in offenders[:60]:
            print(f"- {item}")
    issues = [k for k, v in checks.items() if not v]
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
