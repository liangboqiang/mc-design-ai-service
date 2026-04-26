from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class GitStatusItem:
    path: str
    index_status: str = ""
    worktree_status: str = ""

@dataclass(slots=True)
class GitCommit:
    commit: str
    author: str
    date: str
    message: str
