from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from memory.store import NoteStore
from workspace_paths import data_root, workspace_root


class RepositoryConfigService:
    """Notebook, repository and soft-schema configuration service.

    New UI model: a notebook is the primary governance unit. Built-in notebooks
    point at note.md collections; each notebook can also own source files under a
    workbench path and bind a soft schema / extraction rule.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.data_root = data_root(self.project_root)
        self.config_dir = self.data_root / "config"
        self.schema_dir = self.data_root / "softschemas"
        self.repo_config_path = self.config_dir / "repositories.json"
        self.notebook_config_path = self.config_dir / "notebooks.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_defaults()

    # Legacy repository endpoints kept as thin data config APIs.
    def read_config(self) -> dict[str, Any]:
        return _read_json(self.repo_config_path, self._default_config())

    def save_config(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized = self._normalize_config(config or {})
        self.repo_config_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        self._ensure_repo_dirs(normalized)
        return {"status": "saved", "config": normalized}

    def list_repositories(self) -> dict[str, Any]:
        cfg = self.read_config()
        return {"repositories": cfg.get("repositories", []), "user_workbench": cfg.get("user_workbench", {}), "agent_repository": cfg.get("agent_repository", {})}

    def save_repository(self, repository: dict[str, Any] | None = None) -> dict[str, Any]:
        repository = dict(repository or {})
        repo_id = str(repository.get("repo_id") or repository.get("id") or "").strip()
        if not repo_id:
            raise ValueError("缺少 repo_id")
        cfg = self.read_config()
        repos = [r for r in cfg.get("repositories", []) if r.get("repo_id") != repo_id]
        repos.append(self._normalize_repo(repository))
        repos.sort(key=lambda x: (x.get("repo_type", ""), x.get("repo_id", "")))
        cfg["repositories"] = repos
        self.save_config(cfg)
        return {"status": "saved", "repository": self.get_repository(repo_id).get("repository")}

    def delete_repository(self, repo_id: str = "") -> dict[str, Any]:
        repo_id = str(repo_id or "").strip()
        if not repo_id:
            raise ValueError("缺少 repo_id")
        cfg = self.read_config()
        before = len(cfg.get("repositories", []))
        cfg["repositories"] = [r for r in cfg.get("repositories", []) if r.get("repo_id") != repo_id]
        self.save_config(cfg)
        return {"status": "deleted", "repo_id": repo_id, "removed": before - len(cfg.get("repositories", []))}

    def get_repository(self, repo_id: str = "") -> dict[str, Any]:
        for repo in self.read_config().get("repositories", []):
            if repo.get("repo_id") == repo_id:
                return {"repository": repo}
        return {"repository": None}

    # Notebook APIs.
    def list_notebooks(self) -> dict[str, Any]:
        cfg = self.read_notebook_config()
        notebooks = [self._enrich_notebook(row) for row in cfg.get("notebooks", [])]
        return {"notebooks": notebooks, "count": len(notebooks)}

    def read_notebook_config(self) -> dict[str, Any]:
        if not self.notebook_config_path.exists():
            self.notebook_config_path.write_text(json.dumps(self._default_notebook_config(), ensure_ascii=False, indent=2), encoding="utf-8")
        cfg = _read_json(self.notebook_config_path, self._default_notebook_config())
        cfg["notebooks"] = [self._normalize_notebook(row) for row in cfg.get("notebooks", [])]
        self._ensure_notebook_dirs(cfg)
        return cfg

    def get_notebook(self, notebook_id: str = "") -> dict[str, Any]:
        notebook_id = str(notebook_id or "").strip()
        for row in self.read_notebook_config().get("notebooks", []):
            if row.get("notebook_id") == notebook_id:
                return {"notebook": self._enrich_notebook(row, include_notes=True, include_sources=True)}
        return {"notebook": None}

    def save_notebook(self, notebook: dict[str, Any] | None = None) -> dict[str, Any]:
        notebook = self._normalize_notebook(dict(notebook or {}))
        cfg = self.read_notebook_config()
        rows = [row for row in cfg.get("notebooks", []) if row.get("notebook_id") != notebook["notebook_id"]]
        rows.append(notebook)
        rows.sort(key=lambda x: (x.get("notebook_type", ""), x.get("notebook_id", "")))
        cfg["notebooks"] = rows
        self.notebook_config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        self._ensure_notebook_dirs(cfg)
        return self.get_notebook(notebook["notebook_id"])

    def delete_notebook(self, notebook_id: str = "") -> dict[str, Any]:
        notebook_id = str(notebook_id or "").strip()
        cfg = self.read_notebook_config()
        before = len(cfg.get("notebooks", []))
        cfg["notebooks"] = [row for row in cfg.get("notebooks", []) if row.get("notebook_id") != notebook_id]
        self.notebook_config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "deleted", "notebook_id": notebook_id, "removed": before - len(cfg.get("notebooks", []))}

    # Soft schema APIs.
    def list_soft_schemas(self) -> dict[str, Any]:
        schemas = []
        for path in sorted(self.schema_dir.glob("*.json")):
            data = _read_json(path, {})
            data.setdefault("schema_id", path.stem)
            data.setdefault("path", _rel(self.project_root, path))
            schemas.append(data)
        return {"schemas": schemas}

    def read_soft_schema(self, schema_id: str = "") -> dict[str, Any]:
        schema_id = _safe_id(schema_id or "schema.default")
        path = self.schema_dir / f"{schema_id}.json"
        if not path.exists():
            schema = self._default_schema(schema_id)
            path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"schema": _read_json(path, self._default_schema(schema_id))}

    def save_soft_schema(self, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        schema = dict(schema or {})
        schema_id = _safe_id(str(schema.get("schema_id") or schema.get("id") or "schema.default"))
        schema["schema_id"] = schema_id
        schema.setdefault("name", schema_id)
        schema.setdefault("recommended_fields", [])
        schema.setdefault("recommended_relations", [])
        schema.setdefault("candidate_fields", [])
        schema.setdefault("candidate_relations", [])
        schema["updated_at"] = _now()
        path = self.schema_dir / f"{schema_id}.json"
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "saved", "schema": schema}

    def discover_soft_schema(self, schema_id: str = "schema.default", repo_id: str = "") -> dict[str, Any]:
        schema = self.read_soft_schema(schema_id).get("schema", {})
        known = {str(item.get("name") or item.get("field") or "").strip() for item in schema.get("recommended_fields", [])}
        known |= {str(item.get("name") or item.get("field") or "").strip() for item in schema.get("candidate_fields", [])}
        known = {x for x in known if x}
        notes = NoteStore(self.project_root).list_notes()
        candidates: dict[str, dict[str, Any]] = {}
        for note in notes:
            for key, value in (note.fields or {}).items():
                name = str(key).strip()
                if not name or name in known:
                    continue
                row = candidates.setdefault(name, {"name": name, "count": 0, "examples": [], "status": "candidate", "source": "note_fields"})
                row["count"] += 1
                if len(row["examples"]) < 6:
                    row["examples"].append({"note_id": note.note_id, "title": note.title, "value": str(value)[:160]})
        existing = {str(item.get("name") or "") for item in schema.get("candidate_fields", [])}
        merged = list(schema.get("candidate_fields", []))
        for name, row in sorted(candidates.items(), key=lambda x: (-x[1]["count"], x[0])):
            if name not in existing:
                merged.append(row)
        schema["candidate_fields"] = merged
        schema["last_discovered_at"] = _now()
        self.save_soft_schema(schema)
        return {"schema": schema, "new_candidates": list(candidates.values())}

    def accept_soft_schema_field(self, schema_id: str = "schema.default", field_name: str = "", config: dict[str, Any] | None = None) -> dict[str, Any]:
        field_name = str(field_name or "").strip()
        if not field_name:
            raise ValueError("缺少 field_name")
        schema = self.read_soft_schema(schema_id).get("schema", {})
        recommended = list(schema.get("recommended_fields", []))
        existing = {str(item.get("name") or "") for item in recommended}
        candidate_rows = []
        source_candidate = None
        for item in schema.get("candidate_fields", []):
            if item.get("name") == field_name:
                source_candidate = item
            else:
                candidate_rows.append(item)
        row = {"name": field_name, "aliases": [], "type": "text", "required_for_runtime": False, "evidence_required": True}
        if isinstance(source_candidate, dict):
            row.update({k: v for k, v in source_candidate.items() if k in {"name", "aliases", "type", "unit", "description"}})
        row.update(config or {})
        if field_name not in existing:
            recommended.append(row)
        schema["recommended_fields"] = recommended
        schema["candidate_fields"] = candidate_rows
        return self.save_soft_schema(schema)

    # Internal helpers.
    def _enrich_notebook(self, row: dict[str, Any], include_notes: bool = False, include_sources: bool = False) -> dict[str, Any]:
        notebook = dict(row)
        notes = self._notes_for_notebook(notebook)
        notebook["note_count"] = len(notes)
        notebook["notes_preview"] = notes[:8]
        notebook["summary"] = notebook.get("description") or f"{notebook.get('name')} 共收纳 {len(notes)} 条 note.md。"
        if include_notes:
            notebook["notes"] = notes
        if include_sources:
            notebook["source_files"] = self._source_files_for_notebook(notebook)
        return notebook

    def _notes_for_notebook(self, notebook: dict[str, Any]) -> list[dict[str, Any]]:
        base = str(notebook.get("path") or "").strip().replace("\\", "/").strip("/")
        kind = str(notebook.get("note_kind") or "").strip().lower()
        rows = []
        for note in NoteStore(self.project_root).list_notes():
            path = str(note.path or "").replace("\\", "/")
            if base and not (path.startswith(base.rstrip("/") + "/") or path == base):
                continue
            if kind and str(note.kind or "").lower() != kind:
                continue
            rows.append({
                "note_id": note.note_id,
                "title": note.title,
                "kind": note.kind,
                "status": note.status,
                "maturity": note.maturity,
                "summary": note.summary,
                "path": note.path,
                "tags": list(note.tags),
            })
        return sorted(rows, key=lambda x: (str(x.get("kind")), str(x.get("note_id"))))

    def _source_files_for_notebook(self, notebook: dict[str, Any]) -> list[dict[str, Any]]:
        source_path = str(notebook.get("source_path") or "").replace("\\", "/").strip("/")
        if not source_path:
            return []
        root = _safe_under_project(self.project_root, source_path)
        root.mkdir(parents=True, exist_ok=True)
        rows = []
        for item in sorted(root.rglob("*"), key=lambda p: (p.is_file(), p.as_posix().lower())):
            if item.name.startswith("."):
                continue
            stat = item.stat()
            rows.append({
                "name": item.name,
                "path": item.relative_to(root).as_posix(),
                "kind": "folder" if item.is_dir() else "file",
                "size": 0 if item.is_dir() else stat.st_size,
                "modified_at": _ts(stat.st_mtime),
                "suffix": item.suffix.lower(),
            })
        return rows

    def _normalize_notebook(self, row: dict[str, Any]) -> dict[str, Any]:
        notebook_id = _safe_id(str(row.get("notebook_id") or row.get("id") or row.get("repo_id") or f"notebook.{int(time.time())}"))
        notebook_type = str(row.get("notebook_type") or row.get("type") or "team").strip() or "team"
        path = str(row.get("path") or f"data/notes/custom/{notebook_id.replace('.', '_')}").replace("\\", "/")
        return {
            "notebook_id": notebook_id,
            "name": str(row.get("name") or notebook_id),
            "description": str(row.get("description") or row.get("summary") or ""),
            "notebook_type": notebook_type,
            "path": path,
            "note_kind": str(row.get("note_kind") or row.get("kind") or ""),
            "soft_schema_id": "" if notebook_type == "user" else str(row.get("soft_schema_id") or "schema.business_document"),
            "extraction_rule_id": str(row.get("extraction_rule_id") or "rule.default"),
            "source_path": str(row.get("source_path") or f"data/workbench/team/notebooks/{notebook_id.replace('.', '_')}/sources").replace("\\", "/"),
            "index_mode": str(row.get("index_mode") or "incremental"),
            "icon": str(row.get("icon") or "📒"),
        }

    def _default_notebook_config(self) -> dict[str, Any]:
        return {
            "notebooks": [
                {"notebook_id": "builtin.agent", "name": "智能体笔记本", "description": "系统内置 Agent 笔记集合。", "notebook_type": "builtin", "path": "data/notes/system/agent", "note_kind": "Agent", "soft_schema_id": "schema.agent", "extraction_rule_id": "rule.agent", "source_path": "data/workbench/team/notebooks/builtin_agent/sources", "icon": "🤖"},
                {"notebook_id": "builtin.skill", "name": "技能笔记本", "description": "系统 Skill、能力说明与使用边界。", "notebook_type": "builtin", "path": "data/notes/system/skill", "note_kind": "Skill", "soft_schema_id": "schema.business_document", "extraction_rule_id": "rule.skill", "source_path": "data/workbench/team/notebooks/builtin_skill/sources", "icon": "🧩"},
                {"notebook_id": "builtin.toolbox", "name": "工具箱笔记本", "description": "工具箱级能力与工具集合说明。", "notebook_type": "builtin", "path": "data/notes/system/tool", "note_kind": "Toolbox", "soft_schema_id": "schema.tool", "extraction_rule_id": "rule.toolbox", "source_path": "data/workbench/team/notebooks/builtin_toolbox/sources", "icon": "🧰"},
                {"notebook_id": "builtin.tool", "name": "工具笔记本", "description": "可被 Capability 激活和调度的工具笔记。", "notebook_type": "builtin", "path": "data/notes/system/tool", "note_kind": "Tool", "soft_schema_id": "schema.tool", "extraction_rule_id": "rule.tool", "source_path": "data/workbench/team/notebooks/builtin_tool/sources", "icon": "🔧"},
                {"notebook_id": "builtin.knowledge", "name": "系统知识笔记本", "description": "LLM、平台说明、系统知识与运行背景。", "notebook_type": "builtin", "path": "data/notes/system/knowledge", "note_kind": "knowledge", "soft_schema_id": "schema.business_document", "extraction_rule_id": "rule.knowledge", "source_path": "data/workbench/team/notebooks/builtin_knowledge/sources", "icon": "📚"},
                {"notebook_id": "user.temporary", "name": "用户临时笔记本", "description": "用户会话附件、生成文件和临时 note 候选。", "notebook_type": "user", "path": "data/workbench/user", "note_kind": "", "soft_schema_id": "", "extraction_rule_id": "rule.user_temp", "source_path": "data/workbench/user", "icon": "📎"},
            ]
        }

    def _ensure_notebook_dirs(self, cfg: dict[str, Any]) -> None:
        for row in cfg.get("notebooks", []):
            for key in ("path", "source_path"):
                rel = str(row.get(key) or "").strip()
                if rel:
                    _safe_under_project(self.project_root, rel).mkdir(parents=True, exist_ok=True)

    def _ensure_defaults(self) -> None:
        if not self.repo_config_path.exists():
            self.repo_config_path.write_text(json.dumps(self._default_config(), ensure_ascii=False, indent=2), encoding="utf-8")
        if not self.notebook_config_path.exists():
            self.notebook_config_path.write_text(json.dumps(self._default_notebook_config(), ensure_ascii=False, indent=2), encoding="utf-8")
        for schema_id in ("schema.agent", "schema.part_design", "schema.tool", "schema.business_document"):
            path = self.schema_dir / f"{schema_id}.json"
            if not path.exists():
                path.write_text(json.dumps(self._default_schema(schema_id), ensure_ascii=False, indent=2), encoding="utf-8")
        self._ensure_repo_dirs(self.read_config())
        self._ensure_notebook_dirs(self.read_notebook_config())

    def _default_config(self) -> dict[str, Any]:
        return {
            "agent_repository": {"path": "data/notes/system/agent", "soft_schema_id": "schema.agent"},
            "user_workbench": {"path": "data/workbench/user", "retention_days": 30, "allow_submit_to_team": True},
            "repositories": [
                {"repo_id": "team.default", "name": "团队默认知识仓库", "repo_type": "team", "path": "data/workbench/team", "soft_schema_id": "schema.business_document", "extraction_rule_id": "rule.default", "index_mode": "incremental"},
                {"repo_id": "team.part_design", "name": "零部件设计知识仓库", "repo_type": "team", "path": "data/workbench/team/part_design", "soft_schema_id": "schema.part_design", "extraction_rule_id": "rule.part_document", "index_mode": "incremental"},
                {"repo_id": "system.notes", "name": "系统 Note 仓库", "repo_type": "system", "path": "data/notes", "soft_schema_id": "schema.business_document", "extraction_rule_id": "rule.note", "index_mode": "full"},
            ],
        }

    def _default_schema(self, schema_id: str) -> dict[str, Any]:
        presets = {
            "schema.agent": ["角色定位", "输入", "输出", "推荐技能", "推荐工具"],
            "schema.part_design": ["零件类型", "关键参数", "材料", "工况", "设计约束", "适用对象"],
            "schema.tool": ["工具用途", "输入参数", "输出结果", "权限等级", "执行器引用"],
            "schema.business_document": ["来源", "适用范围", "关键结论", "相关参数", "证据"],
        }
        fields = presets.get(schema_id, ["摘要", "来源", "关系", "证据"])
        return {
            "schema_id": schema_id,
            "name": schema_id.replace("schema.", ""),
            "description": "Soft Schema 只提供推荐抽取字段，不限制智能体额外抽取。",
            "allow_extra_fields": True,
            "allow_extra_relations": True,
            "recommended_fields": [{"name": field, "aliases": [], "type": "text", "required_for_runtime": False, "evidence_required": True} for field in fields],
            "recommended_relations": [
                {"predicate": "uses", "source_kinds": ["Agent", "Skill"], "target_kinds": ["Tool", "Workflow"], "evidence_required": True},
                {"predicate": "depends_on", "source_kinds": ["Part", "Rule", "Document"], "target_kinds": ["Parameter", "Document"], "evidence_required": True},
                {"predicate": "references", "source_kinds": ["Document", "Case", "SOP"], "target_kinds": ["Evidence", "Document"], "evidence_required": True},
            ],
            "candidate_fields": [],
            "candidate_relations": [],
            "updated_at": _now(),
        }

    def _normalize_config(self, cfg: dict[str, Any]) -> dict[str, Any]:
        default = self._default_config()
        rows = cfg.get("repositories", default.get("repositories", []))
        return {
            "agent_repository": cfg.get("agent_repository") or default["agent_repository"],
            "user_workbench": cfg.get("user_workbench") or default["user_workbench"],
            "repositories": [self._normalize_repo(row) for row in rows],
        }

    def _normalize_repo(self, row: dict[str, Any]) -> dict[str, Any]:
        repo_id = _safe_id(str(row.get("repo_id") or row.get("id") or f"repo.{int(time.time())}"))
        repo_type = str(row.get("repo_type") or "team").strip() or "team"
        return {
            "repo_id": repo_id,
            "name": str(row.get("name") or repo_id),
            "repo_type": repo_type,
            "path": str(row.get("path") or f"data/workbench/team/{repo_id.replace('.', '_')}").replace("\\", "/"),
            "soft_schema_id": "" if repo_type == "user" else str(row.get("soft_schema_id") or "schema.business_document"),
            "extraction_rule_id": str(row.get("extraction_rule_id") or "rule.default"),
            "index_mode": str(row.get("index_mode") or "incremental"),
        }

    def _ensure_repo_dirs(self, cfg: dict[str, Any]) -> None:
        paths = [cfg.get("agent_repository", {}).get("path"), cfg.get("user_workbench", {}).get("path")]
        paths += [repo.get("path") for repo in cfg.get("repositories", [])]
        for rel in paths:
            if not rel:
                continue
            _safe_under_project(self.project_root, rel).mkdir(parents=True, exist_ok=True)


def _safe_id(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "").strip())
    return value.strip("._-") or "schema.default"


def _safe_under_project(project_root: Path, rel: str) -> Path:
    root = workspace_root(project_root).resolve()
    target = (root / str(rel).lstrip("/")).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"路径越界：{rel}")
    return target


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _rel(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace_root(project_root)).as_posix()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ts(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(value))
