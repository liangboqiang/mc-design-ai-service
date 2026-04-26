from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .deps import get_workbench

router = APIRouter()

class RollbackPayload(BaseModel):
    commit: str
    author: str = "admin"
    reason: str = ""

@router.get("/truth/status")
def truth_status(page_id: str | None = None, include_worktree: bool = True):
    return get_workbench().truth.truth_status(page_id, include_worktree=include_worktree)

@router.get("/pages/{page_id:path}/history")
def page_history(page_id: str, limit: int = 20):
    return get_workbench().version.page_history(page_id, limit=limit)

@router.get("/pages/{page_id:path}/versions/{commit}")
def read_version(page_id: str, commit: str):
    return get_workbench().version.read_version(page_id, commit)

@router.get("/pages/{page_id:path}/versions/diff")
def diff_versions(page_id: str, from_commit: str, to_commit: str):
    return get_workbench().version.diff_versions(page_id, from_commit, to_commit)

@router.post("/pages/{page_id:path}/rollback-draft")
def rollback_draft(page_id: str, payload: RollbackPayload):
    return get_workbench().version.create_rollback_draft(page_id, payload.commit, author=payload.author, reason=payload.reason)

@router.get("/releases")
def release_history(limit: int = 50, page_id: str | None = None):
    return get_workbench().release.release_history(limit=limit, page_id=page_id)

@router.get("/releases/{release_id}")
def release_detail(release_id: str):
    return get_workbench().release.release_detail(release_id)
