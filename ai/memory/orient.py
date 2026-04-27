from __future__ import annotations

from dataclasses import asdict
from typing import Any

from memory.graph import MemoryGraphProjector
from memory.lens import LensInterpreter
from memory.store import NoteStore
from memory.types import ActivationHint, Diagnostic, EvidenceRef, MemoryCard, MemoryEdge, MemoryNote, MemoryView


class MemoryOrienter:
    def __init__(self, note_store: NoteStore, lens: LensInterpreter, graph: MemoryGraphProjector):
        self.note_store = note_store
        self.lens = lens
        self.graph = graph

    def orient(self, observation: Any, *, limit: int = 8, runtime_state=None) -> MemoryView:  # noqa: ANN001
        task_brief = _task_brief(observation)
        seed_notes = self.note_store.search(task_brief, limit=max(4, limit // 2))
        if len(seed_notes) < 2:
            seed_notes = _merge_notes(seed_notes, self._default_seed_notes(limit=max(4, limit)))
        graph_payload = self.graph.compile(write_store=False, include_hidden=True)
        related_ids = self._expand(seed_notes, graph_payload, depth=1)
        notes = [self.note_store.get(note_id) for note_id in related_ids]
        resolved = [note for note in notes if note is not None]
        system_cards: list[MemoryCard] = []
        business_cards: list[MemoryCard] = []
        diagnostics: list[Diagnostic] = []
        constraints: list[str] = []
        unknowns: list[str] = []
        activation_hints: list[ActivationHint] = []
        citations: list[EvidenceRef] = []
        for note in resolved:
            analysis = self.lens.analyze(note)
            fields = analysis["normalized_fields"]
            diagnostics.extend(Diagnostic(**item) for item in analysis["diagnostics"])
            card = MemoryCard(
                note_id=note.note_id,
                title=note.title,
                kind=note.kind,
                summary=note.summary,
                fields=self._project_fields(note, fields),
                source_refs=list(note.source_refs),
                tags=list(note.tags),
            )
            if note.kind in {"Agent", "Skill", "Tool", "Toolbox", "Workflow", "Policy", "Rule"}:
                system_cards.append(card)
            else:
                business_cards.append(card)
            constraints.extend(self._extract_constraints(fields))
            unknowns.extend(self._extract_unknowns(fields, analysis["diagnostics"]))
            activation_hints.extend(self._activation_hints(note, fields))
            citations.extend(EvidenceRef(evidence_id=ref, title=ref, uri="") for ref in note.source_refs)
        relations = [MemoryEdge(**edge) for edge in graph_payload["visible_edges"] if edge.get("source") in related_ids or edge.get("target") in related_ids]
        if runtime_state is not None:
            last_tool = getattr(runtime_state, "last_tool_result", "")
            if last_tool:
                constraints.append(f"Last tool result available: {str(last_tool)[:160]}")
        return MemoryView(
            task_brief=task_brief,
            system_cards=_dedupe_cards(system_cards),
            business_cards=_dedupe_cards(business_cards),
            constraints=_unique(constraints),
            relations=relations,
            unknowns=_unique(unknowns),
            activation_hints=_dedupe_hints(activation_hints),
            citations=_dedupe_evidence(citations),
            diagnostics=_dedupe_diagnostics(diagnostics),
        )

    def _default_seed_notes(self, *, limit: int) -> list[MemoryNote]:
        notes = self.note_store.list_notes()
        priority_ids = {"agent.memory_native_kernel", "tool.memory_preview_runtime"}

        def rank(note: MemoryNote) -> tuple[int, str]:
            if note.note_id in priority_ids:
                return (0, note.note_id)
            if note.kind == "Agent" and note.maturity in {"runtime_ready", "projectable"}:
                return (1, note.note_id)
            if note.kind in {"Skill", "Tool", "Workflow", "Toolbox"} and note.maturity in {"runtime_ready", "projectable"}:
                return (2, note.note_id)
            if note.status in {"published", "projectable", "runtime_ready"}:
                return (3, note.note_id)
            return (9, note.note_id)

        return sorted(notes, key=rank)[: max(1, int(limit or 8))]

    @staticmethod
    def _expand(seed_notes: list[MemoryNote], graph_payload: dict, *, depth: int) -> list[str]:
        if not seed_notes:
            return []
        node_ids = {note.note_id for note in seed_notes}
        edges = graph_payload.get("edges") or []
        for _ in range(max(1, depth)):
            expanded = set(node_ids)
            for edge in edges:
                source = str(edge.get("source") or "")
                target = str(edge.get("target") or "")
                if source in node_ids:
                    expanded.add(target)
                if target in node_ids:
                    expanded.add(source)
            node_ids = expanded
        return sorted(node_ids)

    @staticmethod
    def _project_fields(note: MemoryNote, fields: dict[str, Any]) -> dict[str, Any]:
        include = ["role", "input", "output", "skills", "tools", "scope", "policy", "summary"]
        out = {key: value for key, value in fields.items() if key in include}
        if not out and note.fields:
            out = {key: value for key, value in list(note.fields.items())[:4]}
        return out

    @staticmethod
    def _extract_constraints(fields: dict[str, Any]) -> list[str]:
        rows: list[str] = []
        for key in ("constraints", "safety", "scope", "policy"):
            value = fields.get(key)
            if isinstance(value, list):
                rows.extend(str(item) for item in value if str(item).strip())
            elif str(value or "").strip():
                rows.append(f"{key}: {value}")
        return rows

    @staticmethod
    def _extract_unknowns(fields: dict[str, Any], diagnostics: list[dict[str, Any]]) -> list[str]:
        rows = [item.get("message", "") for item in diagnostics if str(item.get("code", "")).startswith("runtime_ready")]
        for key in ("unknowns", "gaps"):
            value = fields.get(key)
            if isinstance(value, list):
                rows.extend(str(item) for item in value)
            elif str(value or "").strip():
                rows.append(str(value))
        return [row for row in rows if str(row).strip()]

    @staticmethod
    def _activation_hints(note: MemoryNote, fields: dict[str, Any]) -> list[ActivationHint]:
        hints: list[ActivationHint] = []
        for key in ("tools", "skills"):
            value = fields.get(key) or []
            values = value if isinstance(value, list) else [value]
            for item in values:
                normalized = str(item or "").strip()
                if not normalized:
                    continue
                hints.append(
                    ActivationHint(
                        capability_id=normalized,
                        reason=f"{note.note_id} recommended via {key}",
                        source_note_id=note.note_id,
                        kind="recommended",
                    )
                )
        for relation in note.relations:
            if relation.predicate in {"uses", "can_activate", "can_use"}:
                hints.append(
                    ActivationHint(
                        capability_id=relation.target,
                        reason=f"{note.note_id} relation {relation.predicate}",
                        source_note_id=note.note_id,
                        kind=relation.kind,
                    )
                )
        return hints


def _merge_notes(primary: list[MemoryNote], fallback: list[MemoryNote]) -> list[MemoryNote]:
    seen: set[str] = set()
    rows: list[MemoryNote] = []
    for note in [*primary, *fallback]:
        if note.note_id not in seen:
            seen.add(note.note_id)
            rows.append(note)
    return rows


def _task_brief(observation: Any) -> str:
    if isinstance(observation, str):
        return observation.strip()
    if hasattr(observation, "task_brief"):
        return str(getattr(observation, "task_brief") or "").strip()
    if isinstance(observation, dict):
        return str(observation.get("task_brief") or observation.get("message") or observation.get("query") or "").strip()
    return str(observation or "").strip()


def _unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        normalized = str(item or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def _dedupe_cards(rows: list[MemoryCard]) -> list[MemoryCard]:
    seen: set[str] = set()
    out: list[MemoryCard] = []
    for item in rows:
        if item.note_id not in seen:
            seen.add(item.note_id)
            out.append(item)
    return out


def _dedupe_hints(rows: list[ActivationHint]) -> list[ActivationHint]:
    seen: set[tuple[str, str]] = set()
    out: list[ActivationHint] = []
    for item in rows:
        key = (item.capability_id, item.reason)
        if item.capability_id and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _dedupe_evidence(rows: list[EvidenceRef]) -> list[EvidenceRef]:
    seen: set[str] = set()
    out: list[EvidenceRef] = []
    for item in rows:
        if item.evidence_id and item.evidence_id not in seen:
            seen.add(item.evidence_id)
            out.append(item)
    return out


def _dedupe_diagnostics(rows: list[Diagnostic]) -> list[Diagnostic]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Diagnostic] = []
    for item in rows:
        key = (item.code, item.note_id, item.field)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out
