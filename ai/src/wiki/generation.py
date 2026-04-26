from __future__ import annotations

from protocol.adapter import ProtocolAdapter
from wiki.node import WikiNode


class WikiPageGenerator:
    """Minimal generation/revision facade.

    Real LLM generation can be plugged here. This class keeps the V2 extension
    point explicit: generated Wiki Pages must pass ProtocolAdapter diagnostics
    before they are materialized into the runtime protocol view.
    """

    def diagnose(self, node: WikiNode):
        return ProtocolAdapter().normalize(node).diagnostics
