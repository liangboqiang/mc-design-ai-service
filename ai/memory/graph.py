from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from memory.lens import LensInterpreter
from memory.store import NoteStore
from memory.types import Diagnostic, MemoryEdge, MemoryNote
from workspace_paths import data_root


class MemoryGraphProjector:
    def __init__(self, project_root: Path, note_store: NoteStore, lens: LensInterpreter):
        self.project_root = Path(project_root).resolve()
        self.note_store = note_store
        self.lens = lens
        self.index_root = data_root(self.project_root) / "indexes"

    def compile(self, *, write_store: bool = True, include_hidden: bool = False) -> dict:
        notes = self.note_store.notes()
        nodes = [self._node_row(note) for note in sorted(notes.values(), key=lambda item: item.note_id)]
        edges = self._build_edges(notes)
        diagnostics = self._build_diagnostics(notes, edges)
        visible_edges = [edge for edge in edges if self._visible(edge) or include_hidden]
        payload = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": [asdict(edge) for edge in edges],
            "visible_edges": [asdict(edge) for edge in visible_edges],
            "triples": [self._triple(edge) for edge in edges],
            "diagnostics": [asdict(item) for item in diagnostics],
        }
        if write_store:
            self.index_root.mkdir(parents=True, exist_ok=True)
            (self.index_root / "graph.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def neighbors(self, note_id: str, *, depth: int = 1) -> dict:
        graph = self.compile(write_store=False, include_hidden=True)
        node_ids = {str(note_id or "").strip()}
        for _ in range(max(1, int(depth or 1))):
            expanded = set(node_ids)
            for edge in graph["edges"]:
                source = str(edge.get("source") or "")
                target = str(edge.get("target") or "")
                if source in node_ids:
                    expanded.add(target)
                if target in node_ids:
                    expanded.add(source)
            node_ids = expanded
        return {
            "note_id": str(note_id or ""),
            "nodes": [row for row in graph["nodes"] if row.get("id") in node_ids],
            "edges": [row for row in graph["edges"] if row.get("source") in node_ids and row.get("target") in node_ids],
            "diagnostics": graph["diagnostics"],
        }

    def _build_edges(self, notes: dict[str, MemoryNote]) -> list[MemoryEdge]:
        edges: list[MemoryEdge] = []
        seen: set[tuple[str, str, str, str]] = set()
        for note in notes.values():
            analysis = self.lens.analyze(note)
            relation_specs = analysis["derived_relations"]
            for relation in relation_specs:
                edge = MemoryEdge(
                    edge_id=self._edge_id(note.note_id, relation["predicate"], relation["target"], relation["kind"]),
                    source=note.note_id,
                    target=str(relation["target"]),
                    predicate=str(relation["predicate"]),
                    label=str(relation.get("label") or relation["predicate"]),
                    kind=str(relation.get("kind") or "declared"),
                    status=str(relation.get("status") or "candidate"),
                    confidence=float(relation.get("confidence") or 1.0),
                    evidence=str(relation.get("evidence") or ""),
                    source_note=note.note_id,
                    source_field=relation.get("source_field"),
                )
                key = (edge.source, edge.target, edge.predicate, edge.kind)
                if key not in seen:
                    seen.add(key)
                    edges.append(edge)
            for target in note.links:
                edge = MemoryEdge(
                    edge_id=self._edge_id(note.note_id, "links_to", target, "linked"),
                    source=note.note_id,
                    target=target,
                    predicate="links_to",
                    label="链接到",
                    kind="linked",
                    status="published" if note.status in {"published", "projectable", "runtime_ready", "locked"} else "candidate",
                    confidence=0.8,
                    evidence=f"Body link [[{target}]]",
                    source_note=note.note_id,
                    source_field=None,
                )
                key = (edge.source, edge.target, edge.predicate, edge.kind)
                if key not in seen:
                    seen.add(key)
                    edges.append(edge)
        return sorted(edges, key=lambda item: (item.source, item.predicate, item.target, item.kind))

    def _build_diagnostics(self, notes: dict[str, MemoryNote], edges: list[MemoryEdge]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        adjacency: dict[str, int] = {note_id: 0 for note_id in notes}
        duplicates: set[tuple[str, str, str, str]] = set()
        seen: set[tuple[str, str, str, str]] = set()
        for edge in edges:
            adjacency[edge.source] = adjacency.get(edge.source, 0) + 1
            adjacency[edge.target] = adjacency.get(edge.target, 0) + 1
            key = (edge.source, edge.target, edge.predicate, edge.kind)
            if key in seen:
                duplicates.add(key)
            seen.add(key)
            if edge.target not in notes:
                diagnostics.append(
                    Diagnostic(
                        code="graph.missing_target_note",
                        severity="warning",
                        message=f"关系目标不存在：{edge.source} -> {edge.target}",
                        note_id=edge.source,
                        field=edge.source_field or "",
                    )
                )
            if edge.status == "candidate":
                diagnostics.append(
                    Diagnostic(
                        code="graph.candidate_unreviewed",
                        severity="info",
                        message=f"存在待审核关系：{edge.source} {edge.predicate} {edge.target}",
                        note_id=edge.source,
                    )
                )
        for source, target, predicate, kind in duplicates:
            diagnostics.append(
                Diagnostic(
                    code="graph.duplicate_edge",
                    severity="warning",
                    message=f"重复边：{source} {predicate} {target} ({kind})",
                    note_id=source,
                )
            )
        for note_id, count in adjacency.items():
            if count == 0:
                diagnostics.append(
                    Diagnostic(
                        code="graph.orphan_note",
                        severity="info",
                        message=f"孤立 note：{note_id}",
                        note_id=note_id,
                    )
                )
        for note in notes.values():
            if note.maturity == "runtime_ready" and not any(edge.source == note.note_id and edge.kind == "declared" for edge in edges):
                diagnostics.append(
                    Diagnostic(
                        code="graph.runtime_ready_missing_declared_relation",
                        severity="warning",
                        message="runtime_ready note 缺少 declared 关系。",
                        note_id=note.note_id,
                    )
                )
            if note.kind == "Tool" and not str(note.fields.get("id") or note.note_id).strip():
                diagnostics.append(
                    Diagnostic(
                        code="graph.tool_missing_capability_spec",
                        severity="warning",
                        message="Tool note 缺少 CapabilitySpec 投影主键。",
                        note_id=note.note_id,
                    )
                )
            if note.kind == "Agent" and not any(str(key).lower() in {"policy", "skills", "tools"} for key in note.fields):
                diagnostics.append(
                    Diagnostic(
                        code="graph.agent_missing_runtime_scope",
                        severity="warning",
                        message="Agent note 缺少 Policy 或 CapabilityScope 字段。",
                        note_id=note.note_id,
                    )
                )
            if note.kind not in {"Agent", "Skill", "Tool", "Toolbox", "Workflow"} and not note.source_refs:
                diagnostics.append(
                    Diagnostic(
                        code="graph.business_note_missing_evidence",
                        severity="info",
                        message="业务 note 缺少 source evidence。",
                        note_id=note.note_id,
                    )
                )
        return diagnostics

    @staticmethod
    def _node_row(note: MemoryNote) -> dict:
        return {
            "id": note.note_id,
            "title": note.title,
            "kind": note.kind,
            "status": note.status,
            "maturity": note.maturity,
            "path": note.path,
            "summary": note.summary,
            "tags": list(note.tags),
        }

    @staticmethod
    def _edge_id(source: str, predicate: str, target: str, kind: str) -> str:
        return f"edge.{source}.{predicate}.{target}.{kind}".replace(" ", "_").replace("/", ".")

    @staticmethod
    def _triple(edge: MemoryEdge) -> dict:
        return {
            "subject": edge.source,
            "predicate": edge.predicate,
            "object": edge.target,
            "kind": edge.kind,
            "status": edge.status,
            "evidence": edge.evidence,
        }

    @staticmethod
    def _visible(edge: MemoryEdge) -> bool:
        if edge.kind == "declared" and edge.status == "published":
            return True
        if edge.kind == "runtime" and edge.status == "published":
            return True
        if edge.kind == "inferred" and edge.status == "reviewed":
            return True
        return False
