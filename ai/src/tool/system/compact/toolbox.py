from __future__ import annotations

import json
import time

from tool.stateful import StatefulToolbox


def micro_compact(rows: list[dict], *, keep_turns: int) -> list[dict]:
    if keep_turns <= 0 or len(rows) <= keep_turns:
        return rows
    return rows[-keep_turns:]


def build_summary(rows: list[dict], *, keep_last: int = 12) -> str:
    if not rows:
        return ""
    return "\n".join(f"[{row.get('role')}] {str(row.get('content'))[:300]}" for row in rows[-keep_last:])



class CompactCapability(StatefulToolbox):
    toolbox_name = "compact"

    def executors(self):
        return {
            'compact.now': self._exec_compact_now,
        }

    def _exec_compact_now(self, args: dict):
        return self.compact_now()

    def before_model_call(self) -> None:
        self._micro_compact()
        if self._estimate_size() > self.runtime.settings.auto_compact_threshold:
            self.compact_now()

    def _micro_compact(self) -> None:
        rows = self.runtime.session.history.read()
        compacted = micro_compact(rows, keep_turns=self.runtime.settings.history_keep_turns)
        if len(compacted) < len(rows):
            self.runtime.session.transcripts.append({"ts": time.time(), "type": "micro_compact", "dropped": len(rows) - len(compacted)})
            self.runtime.session.history.replace(compacted)

    def _estimate_size(self) -> int:
        return sum(len(json.dumps(row, ensure_ascii=False)) for row in self.runtime.session.history.read())

    def compact_now(self) -> str:
        rows = self.runtime.session.history.read()
        if not rows:
            return "No history to compact."
        summary = build_summary(rows)
        self.runtime.session.transcripts.append({"ts": time.time(), "type": "full_compact", "rows": rows})
        self.runtime.session.history.replace([{"role": "system", "content": f"[COMPACTED SUMMARY]\n{summary}"}])
        self.runtime.events.emit("compact.performed", summary=summary)
        return "Context compacted."
