from __future__ import annotations

from .types import ProtocolDiagnostic


def has_errors(rows: list[ProtocolDiagnostic]) -> bool:
    return any(row.level == "error" for row in rows)


def render_diagnostics(rows: list[ProtocolDiagnostic]) -> str:
    if not rows:
        return "Protocol diagnostics: clean."
    return "\n".join(
        f"[{row.level}] {row.node_id}: {row.message}" + (f" | repair: {row.repair_hint}" if row.repair_hint else "")
        for row in rows
    )
