from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from memory.types import Proposal, ProposalBatch
from workspace_paths import data_root


class ProposalQueue:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = data_root(self.project_root) / "proposals"
        for name in ("candidate", "reviewed", "accepted", "rejected"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def capture_runtime_step(self, payload: dict[str, Any]) -> ProposalBatch:
        proposal = Proposal(
            proposal_id=f"proposal_{uuid.uuid4().hex[:12]}",
            proposal_type=str(payload.get("proposal_type") or "runtime_hint"),
            status="candidate",
            source=str(payload.get("source") or "runtime"),
            payload=payload,
            evidence_refs=[str(item) for item in payload.get("evidence_refs") or []],
            created_at=_now(),
            review_notes="",
        )
        target = self.root / "candidate" / f"{proposal.proposal_id}.json"
        target.write_text(json.dumps(asdict(proposal), ensure_ascii=False, indent=2), encoding="utf-8")
        return ProposalBatch([proposal])

    def list_proposals(self, status: str = "candidate") -> list[dict[str, Any]]:
        folder = self.root / status
        if not folder.exists():
            return []
        rows = []
        for path in sorted(folder.glob("*.json")):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return rows


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
