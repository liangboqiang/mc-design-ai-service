from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "ai"
for candidate in (ROOT, AI):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    from kernel.loop import KernelService
    from kernel.state import KernelRequest
    from workbench.preview import RuntimePreviewService

    kernel_text = read(AI / "kernel" / "loop.py")
    prompt_text = read(AI / "kernel" / "prompt.py")
    preview = RuntimePreviewService(AI).preview_runtime(task="检查新的 Prompt 结构")
    prompt = preview.get("prompt", "")
    engine = KernelService().build(KernelRequest(agent_id="general_chat", project_root=AI, max_steps=1))
    checks: dict[str, bool] = {}
    checks["old_runtime_dir_removed"] = not (AI / "src" / "runtime").exists()
    checks["old_protocol_dir_removed"] = not (AI / "src" / "protocol").exists()
    checks["kernel_no_transition_import"] = "old kernel" not in kernel_text
    checks["prompt_no_agent_wiki_section"] = "Agent Raw Note" not in prompt_text and "Memory Hub" not in prompt_text
    checks["prompt_has_memory_view"] = "## MemoryView" in prompt
    checks["prompt_has_capability_view"] = "## CapabilityView" in prompt
    checks["engine_chat_ok"] = isinstance(engine.chat("hello"), str)
    issues = [k for k, v in checks.items() if not v]
    print(f"Kernel checks: {sum(checks.values())}/{len(checks)}")
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
