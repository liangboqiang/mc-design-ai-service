from __future__ import annotations

import difflib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from memory import MemoryService
from workbench.version_service import NoteVersionService
from workspace_paths import data_root, workspace_root


class ProposalReviewService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = data_root(self.project_root) / "proposals"
        self.memory = MemoryService(self.project_root)
        self.versions = NoteVersionService(self.project_root)
        for name in ("candidate", "reviewed", "accepted", "rejected", "applied"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def governance_dashboard(self) -> dict[str, Any]:
        graph = self._load_graph_index()
        proposals = {status: len(self.list_proposals(status=status)) for status in ("candidate", "reviewed", "accepted", "rejected", "applied")}
        conflicts = self._conflicts_from_graph(graph)
        return {
            "proposals": proposals,
            "graph": {"nodes": graph.get("node_count", len(graph.get("nodes", []))), "edges": graph.get("edge_count", len(graph.get("edges", []))), "diagnostics": len(graph.get("diagnostics", []))},
            "conflicts": conflicts,
            "version": self.versions.status(),
        }

    def list_proposals(self, status: str = "candidate") -> list[dict]:
        folder = self.root / status
        rows = []
        for path in sorted(folder.glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
                row.setdefault("proposal_id", path.stem)
                row["storage_status"] = status
                rows.append(row)
            except Exception:  # noqa: BLE001
                continue
        return rows

    def read_proposal(self, proposal_id: str, status: str = "") -> dict[str, Any]:
        path = self._find_proposal(proposal_id, preferred=status)
        if not path:
            raise FileNotFoundError(f"Proposal 不存在：{proposal_id}")
        proposal = json.loads(path.read_text(encoding="utf-8"))
        proposal.setdefault("proposal_id", path.stem)
        return {"proposal": proposal, "diff": self.diff_proposal(proposal), "impact": self.impact_analysis(proposal)}

    def diff_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else proposal
        note_id = str(payload.get("target_note_id") or payload.get("note_id") or "")
        new_text = str(payload.get("markdown") or payload.get("new_markdown") or payload.get("content") or "")
        old_text = ""
        path = ""
        if note_id:
            note = self.memory.note_store.get(note_id)
            if note:
                path = note.path
                target = workspace_root(self.project_root) / note.path
                old_text = target.read_text(encoding="utf-8") if target.exists() else ""
        diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile=f"old:{note_id}", tofile=f"proposal:{note_id}", lineterm="")) if new_text else []
        return {"note_id": note_id, "path": path, "diff": diff, "diff_text": "\n".join(diff), "has_change": bool(diff)}

    def impact_analysis(self, proposal: dict[str, Any]) -> dict[str, Any]:
        payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else proposal
        note_id = str(payload.get("target_note_id") or payload.get("note_id") or "")
        graph = self.memory.graph({"write_store": False, "include_hidden": True})
        related_edges = [edge for edge in graph.get("edges", []) if edge.get("source") == note_id or edge.get("target") == note_id]
        diagnostics = [d for d in graph.get("diagnostics", []) if d.get("note_id") == note_id]
        return {
            "note_id": note_id,
            "related_edge_count": len(related_edges),
            "related_edges": related_edges[:20],
            "diagnostics": diagnostics,
            "requires_incremental_graph_update": bool(note_id),
            "requires_full_rebuild": proposal.get("proposal_type") in {"lens_patch", "rule_patch", "bulk_upgrade"},
            "risk_level": "high" if diagnostics else "normal",
        }

    def conflict_report(self) -> dict[str, Any]:
        return self._conflicts_from_graph(self._load_graph_index())

    def review_proposal(self, proposal_id: str, decision: str = "accepted", review_notes: str = "") -> dict:
        source = self._find_proposal(proposal_id, preferred="candidate")
        if source is None:
            source = self._find_proposal(proposal_id)
        if source is None:
            raise FileNotFoundError(f"Proposal 不存在：{proposal_id}")
        payload = json.loads(source.read_text(encoding="utf-8"))
        normalized = decision if decision in {"accepted", "rejected", "reviewed", "applied"} else "reviewed"
        payload["status"] = normalized
        payload["review_notes"] = review_notes
        payload["reviewed_at"] = _now()
        target_folder = self.root / normalized
        target_folder.mkdir(parents=True, exist_ok=True)
        target = target_folder / source.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if source != target:
            source.unlink(missing_ok=True)
        return payload

    def bulk_review_proposals(self, proposal_ids: list[str] | None = None, decision: str = "accepted", review_notes: str = "") -> dict[str, Any]:
        rows = []
        for proposal_id in proposal_ids or []:
            rows.append(self.review_proposal(proposal_id=proposal_id, decision=decision, review_notes=review_notes))
        return {"decision": decision, "count": len(rows), "items": rows}

    def apply_proposal(self, proposal_id: str, status: str = "accepted", commit_message: str = "apply proposal") -> dict[str, Any]:
        source = self._find_proposal(proposal_id, preferred=status)
        if source is None:
            raise FileNotFoundError(f"Proposal 不存在：{proposal_id}")
        proposal = json.loads(source.read_text(encoding="utf-8"))
        payload = proposal.get("payload") if isinstance(proposal.get("payload"), dict) else proposal
        note_id = str(payload.get("target_note_id") or payload.get("note_id") or "")
        markdown = str(payload.get("markdown") or payload.get("new_markdown") or payload.get("content") or "")
        applied: dict[str, Any] = {"proposal_id": proposal_id, "applied_at": _now(), "operations": []}
        if markdown and note_id:
            target = self._note_path(note_id)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(markdown + ("\n" if not markdown.endswith("\n") else ""), encoding="utf-8")
            applied["operations"].append({"type": "write_note", "note_id": note_id, "path": self._rel(target)})
        proposal["status"] = "applied"
        proposal["applied"] = applied
        target_folder = self.root / "applied"
        target_folder.mkdir(parents=True, exist_ok=True)
        (target_folder / source.name).write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
        source.unlink(missing_ok=True)
        self.memory.note_store.refresh()
        indexes = self.memory.compile_indexes()
        commit = self.versions.commit_notes(message=commit_message or f"apply {proposal_id}", author="review", scope=note_id or "proposal")
        return {"status": "applied", "proposal": proposal, "indexes": indexes, "commit": commit}

    def suggest_fix(self, proposal_id: str = "", diagnostic_code: str = "") -> dict[str, Any]:
        if proposal_id:
            data = self.read_proposal(proposal_id)
            impact = data.get("impact", {})
            return {
                "proposal_id": proposal_id,
                "suggestions": [
                    "先查看结构化 Diff，确认 note.md 主体变更是否合理。",
                    "若缺少 Evidence，请在 note.md 的 Evidence 段补充来源。",
                    "若影响 runtime_ready，建议先转 reviewed，补齐字段后再 accepted。",
                ],
                "impact": impact,
            }
        return {"diagnostic_code": diagnostic_code, "suggestions": ["重新运行图谱诊断。", "按 note_id 定位详情页，并创建修复 Proposal。"]}

    def issue_list(self, severity: str = "", kind: str = "") -> dict[str, Any]:
        graph = self._load_graph_index()
        issues: list[dict[str, Any]] = []
        for idx, item in enumerate(graph.get("diagnostics", []) or []):
            code = str(item.get("code") or "graph.diagnostic")
            note_id = str(item.get("note_id") or item.get("source") or item.get("target") or "")
            issues.append(
                {
                    "issue_id": f"graph:{idx}",
                    "kind": "graph",
                    "severity": item.get("severity") or _severity_from_code(code),
                    "code": code,
                    "note_id": note_id,
                    "title": _issue_title(code),
                    "summary": item.get("message") or item.get("summary") or code,
                    "suggestion": _suggestion_for_issue(code),
                    "details": item,
                    "risk_level": _risk_from_code(code),
                }
            )
        for status in ("candidate", "reviewed", "accepted"):
            for proposal in self.list_proposals(status=status):
                pid = proposal.get("proposal_id") or proposal.get("id")
                issues.append(
                    {
                        "issue_id": f"proposal:{pid}",
                        "kind": "proposal",
                        "severity": "normal" if status == "candidate" else "low",
                        "code": f"proposal.{status}",
                        "note_id": (proposal.get("payload") or {}).get("target_note_id") if isinstance(proposal.get("payload"), dict) else proposal.get("note_id", ""),
                        "title": "待治理候选更新",
                        "summary": f"{pid} 处于 {status} 状态，需要审核、应用或归档。",
                        "suggestion": "查看 Diff 与影响分析，低风险项可批量接受；涉及 note_id、执行器或删除操作需逐项确认。",
                        "details": proposal,
                        "risk_level": "normal",
                    }
                )
        if severity:
            issues = [x for x in issues if x.get("severity") == severity]
        if kind:
            issues = [x for x in issues if x.get("kind") == kind]
        by_kind: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for issue in issues:
            by_kind[issue["kind"]] = by_kind.get(issue["kind"], 0) + 1
            by_severity[issue["severity"]] = by_severity.get(issue["severity"], 0) + 1
        return {"count": len(issues), "by_kind": by_kind, "by_severity": by_severity, "issues": issues[:500]}

    def apply_fix(self, issue_id: str = "", fix_mode: str = "proposal", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        issues = self.issue_list().get("issues", [])
        issue = next((item for item in issues if item.get("issue_id") == issue_id), None)
        if issue is None:
            return {"status": "not_found", "issue_id": issue_id}
        if issue.get("kind") == "proposal" and str(issue_id).startswith("proposal:"):
            proposal_id = str(issue_id).split(":", 1)[1]
            if fix_mode == "accept":
                return {"status": "accepted", "result": self.review_proposal(proposal_id, decision="accepted", review_notes="按健康治理建议接受")}
            if fix_mode == "apply":
                return {"status": "applied", "result": self.apply_proposal(proposal_id, status="accepted", commit_message="按健康治理建议应用")}
        return {
            "status": "proposal_suggested",
            "issue": issue,
            "fix_mode": fix_mode,
            "suggestions": [
                issue.get("suggestion") or "查看问题详情后创建修复 Proposal。",
                "自动修复不会直接修改正式 note.md；请先生成修复候选，再通过 Diff 与影响分析确认。",
            ],
        }

    def _load_graph_index(self) -> dict[str, Any]:
        path = data_root(self.project_root) / "indexes" / "graph.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return self.memory.graph({"write_store": False, "include_hidden": True})

    def _conflicts_from_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        diagnostics = graph.get("diagnostics", [])
        conflict_codes = {"graph.missing_target_note", "graph.duplicate_edge", "graph.runtime_ready_missing_declared_relation"}
        conflicts = [item for item in diagnostics if item.get("code") in conflict_codes or "冲突" in str(item.get("message", ""))]
        by_code: dict[str, int] = {}
        for item in conflicts:
            code = str(item.get("code") or "unknown")
            by_code[code] = by_code.get(code, 0) + 1
        return {"count": len(conflicts), "by_code": by_code, "items": conflicts[:200]}

    def _find_proposal(self, proposal_id: str, preferred: str = "") -> Path | None:
        name = proposal_id if proposal_id.endswith(".json") else f"{proposal_id}.json"
        statuses = [preferred] if preferred else []
        statuses += ["candidate", "reviewed", "accepted", "rejected", "applied"]
        for status in [s for s in statuses if s]:
            path = self.root / status / name
            if path.exists():
                return path
        return None

    def _note_path(self, note_id: str) -> Path:
        note = self.memory.note_store.get(note_id)
        if note is not None:
            return workspace_root(self.project_root) / note.path
        return data_root(self.project_root) / "notes" / note_id.replace(".", "/") / "note.md"

    def _rel(self, path: Path) -> str:
        return Path(path).resolve().relative_to(workspace_root(self.project_root)).as_posix()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _severity_from_code(code: str) -> str:
    if "missing_target" in code or "duplicate" in code or "conflict" in code:
        return "high"
    if "runtime_ready" in code or "missing" in code:
        return "normal"
    return "low"


def _risk_from_code(code: str) -> str:
    if "delete" in code or "executor" in code or "note_id" in code:
        return "high"
    if "missing_target" in code or "duplicate" in code or "runtime_ready" in code:
        return "normal"
    return "low"


def _issue_title(code: str) -> str:
    mapping = {
        "graph.missing_target_note": "关系目标缺失",
        "graph.duplicate_edge": "重复关系",
        "graph.runtime_ready_missing_declared_relation": "运行就绪关系不足",
    }
    return mapping.get(code, "健康检查问题")


def _suggestion_for_issue(code: str) -> str:
    if "missing_target" in code:
        return "检查关系目标是否应新建 note.md，或将该关系转为候选并重新绑定目标。"
    if "duplicate" in code:
        return "合并重复关系，保留证据更完整、状态更高的关系。"
    if "runtime_ready" in code:
        return "补齐 declared 关系或降低 maturity，避免运行时引用不稳定能力。"
    if "missing" in code:
        return "进入 Note 详情页补充缺失字段，并提交 note_patch Proposal。"
    return "查看详情、生成修复建议，并通过审核治理应用。"
