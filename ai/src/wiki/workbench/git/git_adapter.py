from __future__ import annotations

import difflib
import hashlib
import subprocess
import time
from pathlib import Path

from .git_models import GitCommit, GitStatusItem


class GitAdapter:
    """Thin Git CLI adapter.

    This layer owns Git primitives only. It intentionally knows nothing
    about page_id, draft_id, release_id, Runtime Anchor, or Wiki semantics.
    """

    def __init__(self, project_root: Path, *, branch: str | None = None):
        self.project_root = Path(project_root).resolve()
        self.branch = branch

    def is_git_repo(self) -> bool:
        return self._run(["git", "rev-parse", "--is-inside-work-tree"]).returncode == 0

    def current_commit(self) -> str:
        result = self._run(["git", "rev-parse", "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return f"nogit_{int(time.time())}"

    def current_branch(self) -> str:
        result = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip() if result.returncode == 0 else ""

    def worktree_status(self) -> list[GitStatusItem]:
        result = self._run(["git", "status", "--porcelain"])
        if result.returncode != 0:
            return []
        rows: list[GitStatusItem] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            status = line[:2]
            path = line[3:].strip()
            rows.append(GitStatusItem(path=path, index_status=status[:1].strip(), worktree_status=status[1:].strip()))
        return rows

    def is_worktree_clean(self) -> bool:
        return not self.worktree_status()

    def file_hash(self, path: str) -> str:
        data = self._safe_path(path).read_bytes()
        return hashlib.sha256(data).hexdigest()

    def diff_text(self, old: str, new: str, *, fromfile: str = "old", tofile: str = "new") -> str:
        return "\\n".join(
            difflib.unified_diff(
                old.splitlines(),
                new.splitlines(),
                fromfile=fromfile,
                tofile=tofile,
                lineterm="",
            )
        )

    def diff_file(self, path: str, ref: str = "HEAD") -> str:
        if not self.is_git_repo():
            return ""
        result = self._run(["git", "diff", ref, "--", path])
        return result.stdout if result.returncode == 0 else ""

    def log_file(self, path: str, limit: int = 20) -> list[GitCommit]:
        if not self.is_git_repo():
            return []
        fmt = "%H%x1f%an%x1f%ai%x1f%s"
        result = self._run(["git", "log", "--follow", f"--max-count={int(limit)}", f"--format={fmt}", "--", path])
        if result.returncode != 0:
            return []
        rows: list[GitCommit] = []
        for line in result.stdout.splitlines():
            parts = line.split("\x1f", 3)
            if len(parts) == 4:
                rows.append(GitCommit(commit=parts[0], author=parts[1], date=parts[2], message=parts[3]))
        return rows

    def show_file(self, path: str, commit: str) -> str:
        if not self.is_git_repo():
            target = self._safe_path(path)
            if target.exists():
                return target.read_text(encoding="utf-8")
            raise FileNotFoundError(path)
        result = self._run(["git", "show", f"{commit}:{path}"])
        if result.returncode != 0:
            raise FileNotFoundError(f"{commit}:{path}")
        return result.stdout

    def commit_files(self, paths: list[str], message: str, author: str | None = None) -> str:
        if not self.is_git_repo():
            return f"nogit_{int(time.time())}"
        clean_paths = [str(p) for p in paths if str(p).strip()]
        if not clean_paths:
            return self.current_commit()
        add = self._run(["git", "add", *clean_paths])
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or add.stdout.strip())
        env = None
        if author:
            env = {
                **__import__("os").environ,
                "GIT_AUTHOR_NAME": author,
                "GIT_COMMITTER_NAME": author,
            }
        commit = self._run(["git", "commit", "-m", message or "wiki publish"], env=env)
        if commit.returncode != 0:
            # Nothing to commit is a stable no-op.
            if "nothing to commit" in (commit.stdout + commit.stderr).lower():
                return self.current_commit()
            raise RuntimeError(commit.stderr.strip() or commit.stdout.strip())
        return self.current_commit()

    def merge_file(self, current_path: str, base_path: str, draft_path: str) -> tuple[str, str]:
        result = self._run(["git", "merge-file", "-p", current_path, base_path, draft_path])
        return result.stdout, result.stderr

    def _safe_path(self, path: str) -> Path:
        target = (self.project_root / path).resolve()
        if not target.is_relative_to(self.project_root):
            raise ValueError(f"Path escapes project root: {path}")
        return target

    def _run(self, args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            cwd=self.project_root,
            text=True,
            capture_output=True,
            env=env,
        )
