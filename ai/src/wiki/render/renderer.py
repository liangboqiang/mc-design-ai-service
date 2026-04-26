from __future__ import annotations

import re

from ..link import WikiLinkResolver


INLINE_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
LINE_LINK_RE = re.compile(r"^(?P<indent>\s*)(?P<bullet>[-*+]\s+)?\[\[(?P<target>[^\]]+)\]\]\s*$")


class WikiLinkRenderer:
    def __init__(self, *, index: dict, catalog: dict):
        self.resolver = WikiLinkResolver(index=index, catalog=catalog)

    def render(self, text: str) -> str:
        rendered: list[str] = []
        for line in text.splitlines():
            match = LINE_LINK_RE.match(line)
            if match:
                target = match.group("target").strip()
                card = self._render_link_card(target, indent=match.group("indent") or "", bullet=bool(match.group("bullet")))
                if card:
                    rendered.extend(card)
                    continue
            rendered.append(self._render_inline_links(line))
        return "\n".join(rendered)

    def describe(self, target: str) -> dict[str, str] | None:
        return self.resolver.describe(target)

    def _render_inline_links(self, line: str) -> str:
        def replace(match: re.Match[str]) -> str:
            target = match.group(1).strip()
            row = self.describe(target)
            if row is None:
                return match.group(0)
            title = row.get("label") or row["title"]
            summary = row["summary"]
            return f"{title} - {summary}" if summary else title

        return INLINE_LINK_RE.sub(replace, line)

    def _render_link_card(self, target: str, *, indent: str, bullet: bool) -> list[str]:
        row = self.describe(target)
        if row is None:
            return []
        title = row["title"]
        summary = row["summary"]
        if bullet:
            lines = [f"{indent}- **{title}**"]
            if summary:
                lines.append(f"{indent}  {summary}")
            return lines
        lines = [f"{indent}**{title}**"]
        if summary:
            lines.append(f"{indent}{summary}")
        return lines
