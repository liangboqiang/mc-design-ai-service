from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+(/|\*|\.\.)",
    r"\bshutdown\b", r"\breboot\b", r"\bsudo\b", r"\bsu\b",
    r"\bmkfs\b", r"\bdd\b", r"\bmount\b", r"\bumount\b",
    r"\bchmod\s+777\b", r"\bchown\b",
    r"\b(?:vim|vi|nano|emacs|less|more|tail\s+-f|top|htop)\b",
    r"\b(?:curl|wget|ssh|scp|ftp|telnet)\b",
]
ALLOWED_PREFIXES = (
    "python ", "python3 ", "py ", "node ", "npm ", "pytest", "ruff", "mypy", "git status", "git diff",
    "git log", "dir", "ls", "pwd", "echo", "type ", "cat ", "find ", "grep ", "rg ",
)


class ShellToolbox:
    """Constrained local command runner for offline checks.

    This is intentionally narrow.  It is for deterministic local validation such
    as syntax checks, project checks, tests, and read-only repository inspection.
    Network access, interactive programs, privilege escalation, and destructive
    commands are blocked.
    """

    toolbox_name = "shell"
    tags = ("builtin", "workspace", "exec")

    def __init__(self, workspace_root: Path | None = None, timeout: int = 120):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.timeout = timeout

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "ShellToolbox":
        return ShellToolbox(workspace_root=workspace_root, timeout=self.timeout)

    def executors(self):
        return {"shell.run": self._exec_shell_run, "shell.check": self._exec_shell_check}

    def _root(self) -> Path:
        if self.workspace_root is None:
            raise ValueError("ShellToolbox workspace not bound yet.")
        return self.workspace_root.resolve()

    def _safe_cwd(self, raw: str | None) -> Path:
        root = self._root()
        cwd = (root / (raw or ".")).resolve()
        if not cwd.is_relative_to(root):
            raise ValueError(f"cwd escapes workspace: {raw}")
        return cwd

    def _validate(self, command: str) -> None:
        normalized = " ".join(str(command or "").strip().split())
        if not normalized:
            raise ValueError("command cannot be empty")
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                raise ValueError(f"Blocked command by safety policy: {pattern}")
        if not normalized.startswith(ALLOWED_PREFIXES):
            raise ValueError("Command is not in the allowed offline command family")

    def _exec_shell_check(self, args: dict[str, Any]):
        command = str(args.get("command", ""))
        self._validate(command)
        return json.dumps({"allowed": True, "command": command}, ensure_ascii=False)

    def _exec_shell_run(self, args: dict[str, Any]):
        command = str(args["command"])
        self._validate(command)
        timeout = max(1, min(int(args.get("timeout", self.timeout) or self.timeout), 300))
        cwd = self._safe_cwd(args.get("cwd"))
        completed = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (completed.stdout + completed.stderr).strip()
        return json.dumps({
            "returncode": completed.returncode,
            "cwd": cwd.relative_to(self._root()).as_posix() or ".",
            "output": output[:50000] if output else "(no output)",
        }, ensure_ascii=False, indent=2)
