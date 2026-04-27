from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any


@dataclass(slots=True)
class RelationHint:
    predicate: str
    target: str
    label: str = ""
    kind: str = "declared"
    status: str = "candidate"
    confidence: float = 1.0
    evidence: str = ""
    source_field: str | None = None


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    source_kind: str
    uri: str
    title: str
    hash: str
    created_at: str
    metadata: dict[str, Any] = dc_field(default_factory=dict)
    extracted_text_path: str | None = None
    linked_note_ids: list[str] = dc_field(default_factory=list)


@dataclass(slots=True)
class MemoryNote:
    note_id: str
    title: str
    kind: str
    status: str
    body: str
    fields: dict[str, Any] = dc_field(default_factory=dict)
    relations: list[RelationHint] = dc_field(default_factory=list)
    source_refs: list[str] = dc_field(default_factory=list)
    tags: list[str] = dc_field(default_factory=list)
    maturity: str = "draft"
    path: str = ""
    summary: str = ""
    links: list[str] = dc_field(default_factory=list)
    lens_id: str = ""
    sections: dict[str, str] = dc_field(default_factory=dict)


@dataclass(slots=True)
class Lens:
    lens_id: str
    applies_to: list[str] = dc_field(default_factory=list)
    suggested_fields: dict[str, Any] = dc_field(default_factory=dict)
    relation_hints: dict[str, Any] = dc_field(default_factory=dict)
    projection_hints: dict[str, Any] = dc_field(default_factory=dict)
    maturity_checks: dict[str, Any] = dc_field(default_factory=dict)


@dataclass(slots=True)
class MemoryEdge:
    edge_id: str
    source: str
    target: str
    predicate: str
    label: str
    kind: str
    status: str
    confidence: float
    evidence: str
    source_note: str
    source_field: str | None = None


@dataclass(slots=True)
class MemoryCard:
    note_id: str
    title: str
    kind: str
    summary: str
    fields: dict[str, Any] = dc_field(default_factory=dict)
    source_refs: list[str] = dc_field(default_factory=list)
    tags: list[str] = dc_field(default_factory=list)


@dataclass(slots=True)
class ActivationHint:
    capability_id: str
    reason: str
    source_note_id: str = ""
    kind: str = "suggested"


@dataclass(slots=True)
class EvidenceRef:
    evidence_id: str
    title: str
    uri: str = ""


@dataclass(slots=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    note_id: str = ""
    field: str = ""
    details: dict[str, Any] = dc_field(default_factory=dict)


@dataclass(slots=True)
class MemoryView:
    task_brief: str
    system_cards: list[MemoryCard] = dc_field(default_factory=list)
    business_cards: list[MemoryCard] = dc_field(default_factory=list)
    constraints: list[str] = dc_field(default_factory=list)
    relations: list[MemoryEdge] = dc_field(default_factory=list)
    unknowns: list[str] = dc_field(default_factory=list)
    activation_hints: list[ActivationHint] = dc_field(default_factory=list)
    citations: list[EvidenceRef] = dc_field(default_factory=list)
    diagnostics: list[Diagnostic] = dc_field(default_factory=list)


@dataclass(slots=True)
class Proposal:
    proposal_id: str
    proposal_type: str
    status: str
    source: str
    payload: dict[str, Any]
    evidence_refs: list[str] = dc_field(default_factory=list)
    created_at: str = ""
    review_notes: str = ""


@dataclass(slots=True)
class ProposalBatch:
    proposals: list[Proposal] = dc_field(default_factory=list)
