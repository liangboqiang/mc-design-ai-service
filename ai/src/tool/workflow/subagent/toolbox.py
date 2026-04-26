from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from tool.stateful import StatefulToolbox


class SubagentCapability(StatefulToolbox):
    toolbox_name = "subagent"

    def executors(self):
        return {
            'subagent.ask': self._exec_subagent_ask,
            'subagent.batch_run': self._exec_subagent_batch_run,
        }

    def _exec_subagent_ask(self, args: dict):
        return self.ask(prompt=str(args['prompt']), skill=args.get('skill'), tools=[str(item) for item in args.get('tools') or []] if args.get('tools') is not None else None, enhancements=[str(item) for item in args.get('enhancements') or []], toolboxes=[str(item) for item in args.get('toolboxes') or []] if args.get('toolboxes') is not None else None, role_name=str(args.get('role_name') or 'subagent'))

    def _exec_subagent_batch_run(self, args: dict):
        return self.batch_run(jobs=[dict(item) for item in args.get('jobs') or []], max_workers=int(args.get('max_workers') or 4))

    def ask(self, *, prompt: str, skill: str | None, tools: list[str] | None, enhancements: list[str] | None, toolboxes: list[str] | None, role_name: str) -> str:
        child = self.runtime.spawn_child(skill=skill, role_name=role_name, tools=self._resolve_tools(tools=tools, enhancements=enhancements, toolboxes=toolboxes))
        return child.chat(prompt)

    def _resolve_tools(self, *, tools: list[str] | None, enhancements: list[str] | None, toolboxes: list[str] | None) -> list[str]:
        if tools is not None:
            return [str(item) for item in tools]
        merged = [*(toolboxes or []), *(enhancements or [])]
        if merged:
            return [str(item) for item in merged]
        return list(self.runtime.runtime_state.installed_toolboxes)

    def batch_run(self, *, jobs: list[dict], max_workers: int = 4) -> str:
        if not jobs:
            return json.dumps({"status": "ok", "results": []}, ensure_ascii=False, indent=2)

        max_workers = max(1, min(int(max_workers or 4), len(jobs), 16))
        results: list[dict | None] = [None] * len(jobs)

        def run_one(index: int, job: dict) -> dict:
            role_name = str(job.get("role_name") or f"subagent_{index + 1:03d}")
            try:
                result = self.ask(
                    prompt=str(job["prompt"]),
                    skill=job.get("skill"),
                    tools=[str(item) for item in job.get("tools") or []] if job.get("tools") is not None else None,
                    enhancements=[str(item) for item in job.get("enhancements") or []] if job.get("enhancements") is not None else None,
                    toolboxes=[str(item) for item in job.get("toolboxes") or []] if job.get("toolboxes") is not None else None,
                    role_name=role_name,
                )
                return {"index": index, "role_name": role_name, "skill": str(job.get("skill") or ""), "ok": True, "result": result}
            except Exception as exc:  # noqa: BLE001
                return {"index": index, "role_name": role_name, "skill": str(job.get("skill") or ""), "ok": False, "error": f"{type(exc).__name__}: {exc}"}

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="subagent_batch") as pool:
            futures = {pool.submit(run_one, index, job): index for index, job in enumerate(jobs)}
            for future in as_completed(futures):
                payload = future.result()
                results[payload["index"]] = payload

        return json.dumps({"status": "ok", "max_workers": max_workers, "results": results}, ensure_ascii=False, indent=2)
