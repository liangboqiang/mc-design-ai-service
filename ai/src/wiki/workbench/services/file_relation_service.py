from __future__ import annotations

import hashlib
import re
import time
from dataclasses import asdict
from pathlib import Path

from .base import WorkbenchService
from .draft_service import WikiDraftService
from .truth_service import WikiTruthService
from wiki.page_state import is_disabled_markdown, is_locked_markdown
from wiki.workbench.git.git_adapter import GitAdapter


SKIP_DIRS = {".git", "__pycache__", ".runtime_data", ".venv", "node_modules"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}


class WikiFileRelationService(WorkbenchService):
    """File-to-wiki relation and page update support."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.git = GitAdapter(project_root)

    def page_file_status(self, page_id: str) -> dict:
        truth = WikiTruthService(self.project_root).read_truth(page_id)
        page_path = self.project_root / truth["source_path"]
        folder = page_path.parent
        deps = self._dependency_files(folder, page_path)
        page_latest = self._latest_commit(truth["source_path"])
        page_date = page_latest.get("date", "")
        rows = []
        requires_update = False
        for dep in deps:
            rel = dep.relative_to(self.project_root).as_posix()
            latest = self._latest_commit(rel)
            worktree_changed = any(item.path == rel for item in self.git.worktree_status())
            old_text = self._show_or_empty(rel, page_latest.get("commit", "HEAD"))
            current_text = self._safe_read(dep)
            patch = self.git.diff_text(old_text, current_text, fromfile=f"{rel}@page_version", tofile=rel) if old_text != current_text else ""
            changed_after_page = bool(latest.get("date") and page_date and latest.get("date") > page_date)
            changed = worktree_changed or changed_after_page or bool(patch)
            requires_update = requires_update or changed
            rows.append({
                "path": rel,
                "hash": _hash(current_text),
                "latest_commit": latest,
                "worktree_changed": worktree_changed,
                "changed_after_page": changed_after_page,
                "changed": changed,
                "diff_from_page_version": patch[:12000],
            })
        return {
            "page_id": page_id,
            "source_path": truth["source_path"],
            "page_latest_commit": page_latest,
            "dependency_count": len(rows),
            "requires_update": requires_update,
            "update_hint": "依赖文件发生变化，建议执行差异化页面更新。" if requires_update else "依赖文件未发现需要更新页面的变化。",
            "dependencies": rows,
        }

    def update_system_page_from_files(self, page_id: str, *, mode: str = "diff", requirements: str = "", author: str = "wiki_agent") -> dict:
        truth = WikiTruthService(self.project_root).read_truth(page_id)
        markdown = truth["markdown"]
        if is_locked_markdown(markdown) or is_disabled_markdown(markdown):
            return {"ok": False, "message": "页面处于锁定或禁用状态，禁止更新。", "page_id": page_id}
        status = self.page_file_status(page_id)
        if not status["requires_update"] and mode != "full":
            return {"ok": True, "message": "未发现依赖变化，不生成更新草稿。", "status": status}
        if not status["page_latest_commit"].get("commit"):
            body = self._full_extract_body(Path(truth["source_path"]).parent.as_posix())
        else:
            body = self._diff_update_body(status, requirements=requirements, mode=mode)
        updated = self._append_or_replace_section(markdown, "页面更新建议", body)
        draft = WikiDraftService(self.project_root).save_draft(page_id, updated, author=author, reason="根据依赖文件变化更新页面")
        return {"ok": True, "draft": draft, "status": status, "mode": mode}

    def generate_user_folder_wikis(self, root_path: str, *, dry_run: bool = True, author: str = "wiki_agent") -> dict:
        root = (self.project_root / root_path).resolve()
        if not root.is_relative_to(self.project_root):
            raise ValueError(f"路径越界：{root_path}")
        if (self.project_root / "src").resolve() in [root, *root.parents]:
            raise ValueError("系统源码目录不允许自动生成 wiki.md；请使用系统页面更新技能。")
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(root_path)

        candidates = []
        folders = [root] + [p for p in root.rglob("*") if p.is_dir()]
        for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
            if self._skip_dir(folder):
                continue
            wiki_path = folder / "wiki.md"
            if wiki_path.exists():
                continue
            if not self._has_direct_files(folder):
                continue
            markdown = self._user_folder_markdown(folder)
            row = {"path": wiki_path.relative_to(self.project_root).as_posix(), "markdown": markdown}
            candidates.append(row)
            if not dry_run:
                wiki_path.write_text(markdown, encoding="utf-8")

        return {"root_path": root_path, "dry_run": dry_run, "generated_count": len(candidates), "candidates": candidates, "author": author}

    def _dependency_files(self, folder: Path, wiki_path: Path) -> list[Path]:
        rows: list[Path] = []

        def walk(path: Path):
            for item in sorted(path.iterdir()):
                if item == wiki_path:
                    continue
                if item.is_dir():
                    if self._skip_dir(item):
                        continue
                    sub_wiki = item / "wiki.md"
                    if sub_wiki.exists():
                        rows.append(sub_wiki)
                    else:
                        walk(item)
                elif item.is_file() and self._is_useful_file(item) and item.name != "wiki.md":
                    rows.append(item)

        walk(folder)
        return rows

    def _full_extract_body(self, folder_rel: str) -> str:
        folder = self.project_root / folder_rel
        rows = []
        for item in self._dependency_files(folder, folder / "wiki.md"):
            rel = item.relative_to(self.project_root).as_posix()
            text = self._safe_read(item)
            rows.append(f"### {rel}\n\n{text[:3000]}")
        return "\n\n".join(rows) if rows else "未发现可用于自动抽取的依赖文件。"

    def _diff_update_body(self, status: dict, *, requirements: str, mode: str) -> str:
        body = [
            f"- 更新模式：{mode}",
            f"- 更新要求：{requirements or '根据依赖文件差异进行页面更新'}",
            f"- 更新提示：{status.get('update_hint')}",
            "",
        ]
        for dep in status.get("dependencies", []):
            if dep.get("changed") or mode == "full":
                body.append(f"### 依赖文件：{dep['path']}")
                body.append("")
                body.append(dep.get("diff_from_page_version") or "文件关系存在变化，但没有可展示差异。")
                body.append("")
        return "\n".join(body).strip()

    def _user_folder_markdown(self, folder: Path) -> str:
        rel = folder.relative_to(self.project_root).as_posix()
        files = [p for p in sorted(folder.iterdir()) if p.is_file() and p.name != "wiki.md" and self._is_useful_file(p)]
        child_wikis = [p / "wiki.md" for p in sorted(folder.iterdir()) if p.is_dir() and (p / "wiki.md").exists()]
        name = folder.name or "用户资料"
        links = "\n".join(f"- [[{p.parent.name}|{p.parent.relative_to(self.project_root).as_posix()}]]" for p in child_wikis) or "- 待补充"
        file_list = "\n".join(f"- {p.name}" for p in files) or "- 待补充"
        return f"""# 业务知识：{name}

摘要：该页面由用户文件目录自动生成，用于汇总目录 `{rel}` 下的资料内容和下级 Wiki 页面。

## 基本信息

- 实体类型：业务知识
- 实体名称：{name}
- 唯一标识：{rel}
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：{_today()}

## 元词条

- 关键词：用户文件、资料目录、自动建页
- 别名：{name}
- 风险等级：低
- 作用范围：{rel}
- 局部关系：目录包含文件与下级页面
- 依赖文件：{len(files)} 个直接文件
- 更新策略：全量生成

## 内容

该页面用于描述用户上传或维护的资料目录。下级目录如果已经存在 `wiki.md`，本页面只引用下级页面，不重复读取下级全部文件。

## 目录文件

{file_list}

## 关联页面

{links}

## 版本信息

- 当前版本：v1
- 最近发布：待发布
- 最近修改人：系统
- 版本来源：Git
"""

    def _append_or_replace_section(self, markdown: str, title: str, body: str) -> str:
        block = f"## {title}\n\n{body.strip()}\n"
        pattern = re.compile(rf"##\s+{re.escape(title)}\s*.*?(?=\n##\s+|\Z)", re.S)
        if pattern.search(markdown):
            return pattern.sub(block.strip(), markdown).rstrip() + "\n"
        return markdown.rstrip() + "\n\n" + block

    def _latest_commit(self, rel_path: str) -> dict:
        rows = self.git.log_file(rel_path, limit=1)
        if not rows:
            return {"commit": "", "date": "", "author": "", "message": ""}
        return asdict(rows[0])

    def _show_or_empty(self, rel_path: str, commit: str) -> str:
        try:
            return self.git.show_file(rel_path, commit) if commit else ""
        except Exception:
            return ""

    def _safe_read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _skip_dir(self, path: Path) -> bool:
        return any(part in SKIP_DIRS for part in path.parts)

    def _is_useful_file(self, path: Path) -> bool:
        return path.is_file() and path.name not in SKIP_SUFFIXES and not path.name.startswith(".")

    def _has_direct_files(self, folder: Path) -> bool:
        return any(p.is_file() and p.name != "wiki.md" and self._is_useful_file(p) for p in folder.iterdir())


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())
