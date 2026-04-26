from __future__ import annotations

from pathlib import Path


class WikiToolbox:
    toolbox_name = "wiki"
    tags = ("builtin", "wiki", "readonly")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "WikiToolbox":
        return WikiToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            'wiki.search': self._exec_wiki_search,
            'wiki.read_page': self._exec_wiki_read_page,
            'wiki.read_source': self._exec_wiki_read_source,
            'wiki.answer': self._exec_wiki_answer,
        }

    def _exec_wiki_search(self, args: dict):
        return self.runtime.wiki.search(str(args['query']), limit=int(args.get('limit') or 20))

    def _exec_wiki_read_page(self, args: dict):
        return self.runtime.wiki.read_page(str(args['page_id']))

    def _exec_wiki_read_source(self, args: dict):
        return self.runtime.wiki.read_source(str(args['page_id']))

    def _exec_wiki_answer(self, args: dict):
        return self.runtime.wiki.answer(str(args['query']), limit=int(args.get('limit') or 5))
