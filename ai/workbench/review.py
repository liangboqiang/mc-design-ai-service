from __future__ import annotations

import json
import shutil
from pathlib import Path

from workspace_paths import data_root


class ProposalReviewService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = data_root(self.project_root) / "proposals"
        for name in ("candidate", "reviewed", "accepted", "rejected"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def list_proposals(self, status: str = "candidate") -> list[dict]:
        folder = self.root / status
        rows = []
        for path in sorted(folder.glob("*.json")):
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return rows

    def review_proposal(self, proposal_id: str, decision: str = "accepted", review_notes: str = "") -> dict:
        source = self.root / "candidate" / f"{proposal_id}.json"
        if not source.exists():
            raise FileNotFoundError(f"Proposal 不存在：{proposal_id}")
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["status"] = decision
        payload["review_notes"] = review_notes
        target_folder = self.root / (decision if decision in {"accepted", "rejected", "reviewed"} else "reviewed")
        target = target_folder / source.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if source != target:
            source.unlink(missing_ok=True)
        return payload
