from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from memory.evidence import EvidenceStore
from memory.graph import MemoryGraphProjector
from memory.lens import LensInterpreter, LensStore
from memory.orient import MemoryOrienter
from memory.proposal import ProposalQueue
from memory.store import NoteStore
from memory.types import ProposalBatch


class MemoryService:
    def __init__(self, project_root: Path, *, session=None):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.session = session
        self.note_store = NoteStore(self.project_root)
        self.lens_store = LensStore(self.project_root)
        self.lens = LensInterpreter(self.lens_store)
        self.graph_projector = MemoryGraphProjector(self.project_root, self.note_store, self.lens)
        self.orienter = MemoryOrienter(self.note_store, self.lens, self.graph_projector)
        self.evidence_store = EvidenceStore(self.project_root, session=session)
        self.proposals = ProposalQueue(self.project_root)

    def ingest(self, source: list[dict] | None) -> str:
        return self.evidence_store.ingest(source)

    def orient(self, observation: Any, policy: Any | None = None, runtime_state=None):  # noqa: ANN001
        return self.orienter.orient(observation, runtime_state=runtime_state)

    def capture(self, step: Any) -> ProposalBatch:  # noqa: ANN001
        payload = step if isinstance(step, dict) else self._runtime_payload(step)
        return self.proposals.capture_runtime_step(payload)

    def project(self, note_ids: list[str], target: str) -> dict:
        notes = [self.note_store.get(note_id) for note_id in note_ids]
        return {
            "target": target,
            "notes": [self.note_store.to_row(note) for note in notes if note is not None],
        }

    def search(self, query: str, policy: Any | None = None) -> list[dict]:  # noqa: ANN001
        limit = int((policy or {}).get("limit", 20)) if isinstance(policy, dict) else 20
        return [self.note_store.to_row(note) for note in self.note_store.search(query, limit=limit)]

    def graph(self, policy: Any | None = None) -> dict:  # noqa: ANN001
        write_store = True if policy is None else bool((policy or {}).get("write_store", True))
        include_hidden = bool((policy or {}).get("include_hidden", False)) if isinstance(policy, dict) else False
        return self.graph_projector.compile(write_store=write_store, include_hidden=include_hidden)

    def graph_neighbors(self, note_id: str, *, depth: int = 1) -> dict:
        return self.graph_projector.neighbors(note_id, depth=depth)

    def list_notes(self, query: str = "", *, limit: int = 100, kind: str = "") -> list[dict]:
        notes = self.note_store.search(query, limit=limit, kind=kind) if query or kind else self.note_store.list_notes()[:limit]
        return [self.note_store.to_row(note) for note in notes]

    def read_note(self, note_id: str) -> dict | None:
        note = self.note_store.get(note_id)
        return None if note is None else self.note_store.to_row(note)

    def check_note(self, note_id: str) -> dict:
        note = self.note_store.get(note_id)
        if note is None:
            raise KeyError(f"Note not found: {note_id}")
        analysis = self.lens.analyze(note)
        return {
            "note": self.note_store.to_row(note),
            "diagnostics": analysis["diagnostics"],
            "lens": analysis["lens"],
            "normalized_fields": analysis["normalized_fields"],
            "derived_relations": analysis["derived_relations"],
            "runtime_ready": analysis["runtime_ready"],
        }

    def list_lenses(self) -> list[dict]:
        return self.lens_store.list_rows()

    def check_runtime_ready(self, note_id: str) -> dict:
        result = self.check_note(note_id)
        return {
            "note_id": note_id,
            "runtime_ready": result["runtime_ready"],
            "blocking_diagnostics": [item for item in result["diagnostics"] if item.get("severity") == "error"],
        }

    def compile_indexes(self) -> dict:
        indexes = self.note_store.write_indexes()
        graph = self.graph_projector.compile(write_store=True, include_hidden=True)
        return {"indexes": indexes, "graph": graph}

    def state_fragments(self) -> list[str]:
        return self.evidence_store.state_fragments()

    def summary(self) -> str:
        count = len(self.note_store.notes())
        return f"Memory native store: {count} note(s), note.md preferred, wiki.md compatible."

    @staticmethod
    def _runtime_payload(step: Any) -> dict[str, Any]:  # noqa: ANN401
        observation = getattr(step, "observation", "")
        reply = getattr(step, "reply", None)
        tool_results = getattr(step, "tool_results", [])
        memory_view = getattr(step, "memory_view", None)
        capability_view = getattr(step, "capability_view", None)
        assistant_message = ""
        if isinstance(reply, dict):
            assistant_message = str(reply.get("assistant_message") or "")
        elif reply is not None:
            assistant_message = getattr(reply, "assistant_message", "")
        return {
            "proposal_type": "runtime_hint",
            "source": "runtime",
            "observation": str(observation or ""),
            "assistant_message": assistant_message,
            "tool_results": [str(item) for item in tool_results],
            "memory_view": asdict(memory_view) if memory_view is not None else {},
            "capability_view": asdict(capability_view) if capability_view is not None else {},
        }
