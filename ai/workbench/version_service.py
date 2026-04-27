from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from workspace_paths import data_root, workspace_root


class NoteVersionService:
    """Small Git-like version store for note.md.

    It uses immutable snapshots and commit metadata. The interface mirrors the
    git mental model: working tree, commit, history, diff, tag/release, restore.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.data_root = data_root(self.project_root)
        self.notes_root = self.data_root / "notes"
        self.repo_root = self.data_root / "repo" / "notes"
        self.commits_root = self.repo_root / "commits"
        self.refs_root = self.repo_root / "refs"
        self.releases_root = self.data_root / "releases"
        for path in (self.commits_root, self.refs_root, self.releases_root):
            path.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict[str, Any]:
        head = self._head_commit_id()
        current = self._fast_tree_hash(self.notes_root)
        head_hash = self._commit_meta(head).get("tree_hash") if head else ""
        if head:
            changed = self._changed_files_by_stat(self.commits_root / head / "snapshot", self.notes_root)
        else:
            changed = [p.relative_to(self.notes_root).as_posix() for p in self.notes_root.rglob("note.md")]
        return {
            "head": head,
            "working_tree_hash": current,
            "head_tree_hash": head_hash,
            "dirty": current != head_hash,
            "changed_files": changed,
            "notes_root": self._rel(self.notes_root),
            "repo_root": self._rel(self.repo_root),
        }

    def commit_notes(self, message: str = "manual note commit", author: str = "system", scope: str = "all") -> dict[str, Any]:
        commit_id = f"commit_{time.strftime('%Y%m%d%H%M%S', time.gmtime())}_{uuid.uuid4().hex[:8]}"
        target = self.commits_root / commit_id
        snapshot = target / "snapshot"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        if snapshot.exists():
            shutil.rmtree(snapshot)
        shutil.copytree(self.notes_root, snapshot, ignore=shutil.ignore_patterns("__pycache__"))
        parent = self._head_commit_id()
        meta = {
            "commit_id": commit_id,
            "parent": parent,
            "message": message or "manual note commit",
            "author": author or "system",
            "scope": scope or "all",
            "created_at": _now(),
            "tree_hash": self._tree_hash(snapshot),
            "changed_files": self._changed_files(self.commits_root / parent / "snapshot", snapshot) if parent else [p.relative_to(snapshot).as_posix() for p in snapshot.rglob("note.md")],
        }
        (target / "commit.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.refs_root / "HEAD").write_text(commit_id, encoding="utf-8")
        return meta

    def list_commits(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.commits_root.glob("commit_*/commit.json"), reverse=True):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return rows[: max(1, int(limit or 50))]

    def note_history(self, note_path: str = "", note_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
        rel = self._note_rel(note_path=note_path, note_id=note_id)
        rows = []
        for meta in self.list_commits(limit=500):
            if (self.commits_root / meta["commit_id"] / "snapshot" / rel).exists() or rel in meta.get("changed_files", []):
                rows.append(meta)
        return rows[: max(1, int(limit or 50))]

    def read_note_at_commit(self, commit_id: str, note_path: str = "", note_id: str = "") -> dict[str, Any]:
        rel = self._note_rel(note_path=note_path, note_id=note_id)
        target = self.commits_root / commit_id / "snapshot" / rel
        if not target.exists():
            raise FileNotFoundError(f"版本中不存在 note：{rel}")
        return {"commit_id": commit_id, "path": rel, "content": target.read_text(encoding="utf-8")}

    def diff_note_versions(self, note_path: str = "", note_id: str = "", from_commit: str = "", to_commit: str = "WORKTREE") -> dict[str, Any]:
        rel = self._note_rel(note_path=note_path, note_id=note_id)
        old_text = self._read_version_file(from_commit, rel)
        new_text = self._read_version_file(to_commit, rel)
        diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile=from_commit or "EMPTY", tofile=to_commit or "WORKTREE", lineterm=""))
        return {"path": rel, "from": from_commit, "to": to_commit, "diff": diff, "diff_text": "\n".join(diff)}

    def restore_note_version(self, note_path: str = "", note_id: str = "", commit_id: str = "", message: str = "restore note version") -> dict[str, Any]:
        if not commit_id:
            raise ValueError("缺少 commit_id")
        rel = self._note_rel(note_path=note_path, note_id=note_id)
        source = self.commits_root / commit_id / "snapshot" / rel
        if not source.exists():
            raise FileNotFoundError(f"版本中不存在 note：{rel}")
        target = self.notes_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        commit = self.commit_notes(message=message or f"restore {rel} from {commit_id}", author="version-service", scope=rel)
        return {"status": "restored", "path": rel, "source_commit": commit_id, "new_commit": commit}

    def create_release(self, name: str = "", message: str = "") -> dict[str, Any]:
        head = self._head_commit_id()
        if not head or self.status().get("dirty"):
            meta = self.commit_notes(message=message or "release snapshot", author="release-service", scope="release")
            head = meta["commit_id"]
        release_id = name.strip() or f"release_{time.strftime('%Y%m%d%H%M%S', time.gmtime())}"
        release_dir = self.releases_root / release_id
        if release_dir.exists():
            shutil.rmtree(release_dir)
        release_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.commits_root / head / "snapshot", release_dir / "notes")
        payload = {"release_id": release_id, "commit_id": head, "message": message, "created_at": _now()}
        (release_dir / "release.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.refs_root / f"release_{release_id}").write_text(head, encoding="utf-8")
        return payload

    def list_releases(self) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.releases_root.glob("*/release.json"), reverse=True):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return rows

    def rollback_release(self, release_id: str, message: str = "rollback release") -> dict[str, Any]:
        release_dir = self.releases_root / release_id / "notes"
        if not release_dir.exists():
            raise FileNotFoundError(f"Release 不存在：{release_id}")
        backup = self.commit_notes(message=f"pre-rollback backup before {release_id}", author="release-service", scope="rollback-backup")
        if self.notes_root.exists():
            shutil.rmtree(self.notes_root)
        shutil.copytree(release_dir, self.notes_root)
        commit = self.commit_notes(message=message or f"rollback to {release_id}", author="release-service", scope="rollback")
        return {"status": "rolled_back", "release_id": release_id, "backup_commit": backup, "new_commit": commit}

    def _fast_tree_hash(self, root: Path) -> str:
        digest = hashlib.sha256()
        if not root.exists():
            return digest.hexdigest()
        for path in sorted(p for p in root.rglob("note.md") if p.is_file()):
            stat = path.stat()
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(str(stat.st_size).encode("ascii"))
            digest.update(str(int(stat.st_mtime)).encode("ascii"))
        return digest.hexdigest()

    def _changed_files_by_stat(self, old_root: Path, new_root: Path) -> list[str]:
        old = _file_stats(old_root) if old_root.exists() else {}
        new = _file_stats(new_root) if new_root.exists() else {}
        return [path for path in sorted(set(old) | set(new)) if old.get(path) != new.get(path)]

    def _read_version_file(self, commit_id: str, rel: str) -> str:
        if not commit_id or commit_id == "EMPTY":
            return ""
        if commit_id == "WORKTREE":
            target = self.notes_root / rel
        else:
            target = self.commits_root / commit_id / "snapshot" / rel
        return target.read_text(encoding="utf-8") if target.exists() else ""

    def _note_rel(self, note_path: str = "", note_id: str = "") -> str:
        if note_path:
            rel = str(note_path).replace("\\", "/").strip("/")
            if rel.startswith("data/notes/"):
                rel = rel[len("data/notes/") :]
            if rel.endswith("note.md"):
                return rel
        if note_id:
            return f"{str(note_id).strip().replace('.', '/')}/note.md"
        raise ValueError("缺少 note_path 或 note_id")

    def _head_commit_id(self) -> str:
        head = self.refs_root / "HEAD"
        return head.read_text(encoding="utf-8").strip() if head.exists() else ""

    def _commit_meta(self, commit_id: str) -> dict[str, Any]:
        if not commit_id:
            return {}
        path = self.commits_root / commit_id / "commit.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _changed_files(self, old_root: Path, new_root: Path) -> list[str]:
        old = _file_hashes(old_root) if old_root.exists() else {}
        new = _file_hashes(new_root) if new_root.exists() else {}
        paths = sorted(set(old) | set(new))
        return [path for path in paths if old.get(path) != new.get(path)]

    def _tree_hash(self, root: Path) -> str:
        digest = hashlib.sha256()
        for rel, value in sorted(_file_hashes(root).items()):
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(value.encode("ascii"))
            digest.update(b"\0")
        return digest.hexdigest()

    def _rel(self, path: Path) -> str:
        try:
            return Path(path).resolve().relative_to(workspace_root(self.project_root)).as_posix()
        except Exception:  # noqa: BLE001
            return Path(path).as_posix()


def _file_hashes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    if not root.exists():
        return rows
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in rel:
            continue
        rows[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _file_stats(root: Path) -> dict[str, tuple[int, int]]:
    rows: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return rows
    for path in sorted(p for p in root.rglob("note.md") if p.is_file()):
        stat = path.stat()
        rows[path.relative_to(root).as_posix()] = (stat.st_size, int(stat.st_mtime))
    return rows
