from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI, AI / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    from workbench.preview import RuntimePreviewService

    kernel_text = read(AI / "src/runtime/kernel.py")
    prompt_text = read(AI / "src/runtime/prompt.py")
    preview = RuntimePreviewService(AI).preview_runtime(task="检查新的 Prompt 结构")
    prompt = preview.get("prompt", "")
    checks: dict[str, bool] = {}
    checks["kernel_no_wikihub_import"] = "from wiki.hub import WikiHub" not in kernel_text
    checks["prompt_no_agent_wiki_section"] = "Agent Wiki" not in prompt_text and "Wiki Hub" not in prompt_text
    checks["prompt_has_memory_view"] = "## MemoryView" in prompt
    checks["prompt_has_capability_view"] = "## CapabilityView" in prompt
    checks["prompt_has_no_raw_frontmatter"] = "---" not in prompt
    issues = [k for k, v in checks.items() if not v]
    print(f"Kernel checks: {sum(checks.values())}/{len(checks)}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
