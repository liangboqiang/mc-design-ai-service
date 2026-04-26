from __future__ import annotations

from tool.stateful import StatefulToolbox


class TodoCapability(StatefulToolbox):
    toolbox_name = "todo"
    store_name = "todo.json"

    def bind_runtime(self, runtime, tool_lookup=None) -> None:
        super().bind_runtime(runtime, tool_lookup)
        if self.runtime.session.read_state_json(self.store_name, None) is None:
            self.runtime.session.write_state_json(self.store_name, {"items": []})

    def _render(self) -> str:
        payload = self.runtime.session.read_state_json(self.store_name, {"items": []})
        lines = []
        for item in payload["items"]:
            icon = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}.get(item["status"], "[?]")
            lines.append(f"{icon} {item['id']}: {item['text']}")
        return "\n".join(lines) or "(empty todo list)"

    def executors(self):
        return {
            'todo.update': self._exec_todo_update,
            'todo.view': self._exec_todo_view,
        }

    def _exec_todo_update(self, args: dict):
        return self._update(args['items'])

    def _exec_todo_view(self, args: dict):
        return self._render()

    def _update(self, items: list[dict]) -> str:
        in_progress_count = sum(1 for item in items if item.get("status") == "in_progress")
        if in_progress_count > 1:
            raise ValueError("Only one todo item can be in_progress.")
        normalized = [
            {
                "id": item.get("id") or str(index),
                "text": str(item["text"]),
                "status": str(item.get("status") or "pending"),
            }
            for index, item in enumerate(items, start=1)
        ]
        self.runtime.session.write_state_json(self.store_name, {"items": normalized})
        return self._render()

    def state_fragments(self) -> list[str]:
        return [f"todo:\n{self._render()}"]
