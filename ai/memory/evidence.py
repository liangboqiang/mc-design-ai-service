from __future__ import annotations

import hashlib
import json
import shutil
import time
import urllib.request
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from memory.types import EvidenceRecord
from workspace_paths import data_root


ATTACHMENT_INGEST_STATE = "attachment_ingest.json"


class EvidenceStore:
    def __init__(self, project_root: Path, session=None):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.session = session
        self.root = data_root(self.project_root) / "evidence"
        self.upload_root = self.root / "uploads"
        self.records_root = self.root / "records"
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.records_root.mkdir(parents=True, exist_ok=True)

    def ingest(self, files: list[dict] | None) -> str:
        files = files or []
        created: list[dict] = []
        for index, item in enumerate(files, start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"upload_{index}")
            uri = str(item.get("url") or item.get("path") or "")
            if item.get("content") is not None:
                record = self._store_one_with_content(name=name, uri=uri, content=str(item.get("content") or ""))
            else:
                record = self._store_one(name=name, uri=uri)
            created.append(asdict(record))
        payload = {"status": "ok", "count": len(created), "records": created}
        self._write_state(payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def state_fragments(self) -> list[str]:
        if self.session is None:
            return []
        snapshot = self.session.read_state_json(ATTACHMENT_INGEST_STATE, {}) or {}
        if not snapshot:
            return []
        return [
            (
                "Memory evidence state -> "
                f"updated_at={snapshot.get('updated_at', '')}; "
                f"count={snapshot.get('count', 0)}; "
                f"titles={', '.join(snapshot.get('titles') or []) or '(none)'}"
            )
        ]

    def _store_one(self, *, name: str, uri: str) -> EvidenceRecord:
        normalized_name = Path(name).name or "upload.bin"
        target = self.upload_root / normalized_name
        digest = hashlib.sha1(f"{normalized_name}|{uri}|{time.time()}".encode("utf-8")).hexdigest()[:16]
        status = self._copy_to_target(uri=uri, target=target)
        record = EvidenceRecord(
            evidence_id=f"evidence.upload.{digest}",
            source_kind="upload",
            uri=uri,
            title=normalized_name,
            hash=digest,
            created_at=_now(),
            metadata={"status": status, "stored_path": target.as_posix() if target.exists() else ""},
        )
        (self.records_root / f"{record.evidence_id}.json").write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def _copy_to_target(self, *, uri: str, target: Path) -> str:
        parsed = urlparse(uri)
        try:
            if parsed.scheme in {"http", "https"}:
                with urllib.request.urlopen(uri, timeout=20) as response:  # noqa: S310
                    target.write_bytes(response.read())
                return "stored"
            source = Path(uri.replace("file://", "")).expanduser()
            if source.exists():
                shutil.copy2(source, target)
                return "stored"
            return "metadata_only"
        except Exception as exc:  # noqa: BLE001
            return f"error:{exc.__class__.__name__}"

    def _store_one_with_content(self, *, name: str, uri: str, content: str) -> EvidenceRecord:
        normalized_name = Path(name).name or "upload.txt"
        target = self.upload_root / normalized_name
        target.write_text(str(content or ""), encoding="utf-8")
        digest = hashlib.sha1(f"{normalized_name}|{time.time()}".encode("utf-8")).hexdigest()[:16]
        record = EvidenceRecord(
            evidence_id=f"evidence.upload.{digest}",
            source_kind="upload",
            uri=uri,
            title=normalized_name,
            hash=digest,
            created_at=_now(),
            metadata={"status": "stored", "stored_path": target.as_posix()},
        )
        (self.records_root / f"{record.evidence_id}.json").write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def _write_state(self, payload: dict) -> None:
        if self.session is None:
            return
        self.session.write_state_json(
            ATTACHMENT_INGEST_STATE,
            {
                "updated_at": _now(),
                "count": payload.get("count", 0),
                "titles": [row.get("title", "") for row in payload.get("records", [])],
                "payload": payload,
            },
        )


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
