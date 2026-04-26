from __future__ import annotations

import json
import threading
import time

from tool.stateful import StatefulToolbox


class TeamCapability(StatefulToolbox):
    toolbox_name = "team"
    roster_file = "team_roster.json"

    def bind_runtime(self, runtime, tool_lookup=None) -> None:
        super().bind_runtime(runtime, tool_lookup)
        if self.runtime.session.read_state_json(self.roster_file, None) is None:
            self.runtime.session.write_state_json(self.roster_file, {"members": []})
        self.threads: dict[str, threading.Thread] = {}

    def executors(self):
        return {
            'team.spawn_worker': self._exec_team_spawn_worker,
            'team.list_workers': self._exec_team_list_workers,
            'team.send_message': self._exec_team_send_message,
            'team.read_inbox': self._exec_team_read_inbox,
            'team.broadcast': self._exec_team_broadcast,
        }

    def _exec_team_spawn_worker(self, args: dict):
        return self.spawn_worker(args['name'], args['skill'], args['prompt'], [str(item) for item in args.get('tools') or []] if args.get('tools') is not None else [str(item) for item in args.get('enhancements') or []] or list(self.runtime.runtime_state.installed_toolboxes))

    def _exec_team_list_workers(self, args: dict):
        return json.dumps(self._roster(), ensure_ascii=False, indent=2)

    def _exec_team_send_message(self, args: dict):
        return self.send_message(args['to'], args['content'])

    def _exec_team_read_inbox(self, args: dict):
        return self.read_inbox('lead')

    def _exec_team_broadcast(self, args: dict):
        return self.broadcast(args['content'])

    def _roster(self) -> list[dict]:
        return list(self.runtime.session.read_state_json(self.roster_file, {"members": []})["members"])

    def _save_roster(self, rows: list[dict]) -> None:
        self.runtime.session.write_state_json(self.roster_file, {"members": rows})

    def send_message(self, to: str, content: str, message_type: str = "message", extra: dict | None = None) -> str:
        payload = {"type": message_type, "from": self.runtime.engine_id, "content": content, "ts": time.time()}
        if extra:
            payload.update(extra)
        self.runtime.session.inbox.append(to, payload)
        return f"sent to {to}"

    def read_inbox(self, name: str) -> str:
        rows = self.runtime.session.inbox.drain(name)
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def broadcast(self, content: str) -> str:
        for member in self._roster():
            self.send_message(member["name"], content, message_type="broadcast")
        return "broadcast sent"

    def spawn_worker(self, name: str, skill: str, prompt: str, tools: list[str]) -> str:
        members = self._roster()
        if any(item["name"] == name for item in members):
            raise ValueError(f"Worker already exists: {name}")
        members.append({"name": name, "skill": skill, "status": "working", "tools": tools})
        self._save_roster(members)
        worker = self.runtime.spawn_child(skill=skill, role_name=name, tools=tools)
        thread = threading.Thread(target=self._worker_loop, args=(worker, name, prompt, "autonomy" in tools), daemon=True)
        thread.start()
        self.threads[name] = thread
        self.runtime.events.emit("team.worker_spawned", worker=name, skill=skill)
        return f"worker {name} spawned"

    def _worker_loop(self, worker, name: str, prompt: str, has_autonomy: bool) -> None:  # noqa: ANN001
        worker.chat(prompt)
        while True:
            inbox_rows = self.runtime.session.inbox.drain(name)
            if inbox_rows:
                for row in inbox_rows:
                    response = worker.chat(row["content"])
                    self.runtime.session.inbox.append("lead", {"type": "worker_response", "from": name, "content": response, "ts": time.time()})
            elif has_autonomy:
                worker.tick()
                time.sleep(1.5)
            else:
                time.sleep(1.5)

    def before_user_turn(self, message: str) -> None:
        lead_messages = self.runtime.session.inbox.read_all("lead")
        if lead_messages:
            self.runtime.session.history.append_system(f"<team_inbox>\n{json.dumps(lead_messages, ensure_ascii=False, indent=2)}\n</team_inbox>")
            self.runtime.session.inbox.drain("lead")

    def state_fragments(self) -> list[str]:
        members = self._roster()
        if not members:
            return ["team: (no workers)"]
        return ["team:\n" + "\n".join(f"- {m['name']} | skill={m['skill']} | status={m['status']}" for m in members)]
