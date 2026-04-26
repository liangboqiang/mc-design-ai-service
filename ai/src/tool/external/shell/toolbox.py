from __future__ import annotations

import subprocess
from pathlib import Path


class ShellToolbox:
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
        return {
            'shell.run': self._exec_shell_run,
        }

    def _exec_shell_run(self, args: dict):
        return self._run(args['command'])

    def _run(self, command: str) -> str:
        if self.workspace_root is None:
            raise ValueError("ShellToolbox workspace not bound yet.")
        blocked = ["rm -rf /", "shutdown", "reboot", "sudo "]
        if any(token in command for token in blocked):
            raise ValueError("Blocked dangerous shell command.")
        completed = subprocess.run(
            command,
            shell=True,
            cwd=self.workspace_root,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        output = (completed.stdout + completed.stderr).strip()
        return output[:50000] if output else "(no output)"
