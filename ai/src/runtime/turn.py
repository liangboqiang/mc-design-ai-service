from __future__ import annotations

from kernel.state import RuntimeStep as MemoryRuntimeStep
from .dispatcher import ToolExecutionResult
from .reply_parser import ReplyParser


class TurnLoop:
    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel
        self.parser = ReplyParser()

    def run(self, message: str, files: list[dict] | None = None) -> str:
        self.begin(message, files)
        final = ""
        for step in range(self.kernel.settings.max_steps):
            self.kernel.runtime_state.step = step + 1
            memory_view = self.kernel.memory.orient(message, runtime_state=self.kernel.runtime_state)
            self.kernel.runtime_state.last_memory_view = memory_view
            surface = self.kernel.surface.resolve(observation=message, memory_view=memory_view)
            packet = self.kernel.prompt.compile(surface)
            raw = self.kernel.llm.complete(packet.system_prompt, packet.messages)
            reply = self.parser.parse(raw)
            self.kernel.audit.record("llm.response", raw=raw, tool_calls=len(reply.tool_calls))
            if reply.assistant_message:
                final = reply.assistant_message
                self.kernel.session.history.append_assistant(final)
            if not reply.tool_calls:
                self.kernel.memory.capture(
                    MemoryRuntimeStep(
                        observation=message,
                        memory_view=memory_view,
                        capability_view=surface.capability_view,
                        reply=reply,
                        tool_results=[],
                    )
                )
                self.kernel.events.emit("model.turn.completed", final_answer=final)
                return final
            tool_results: list[ToolExecutionResult] = []
            for call in reply.tool_calls:
                result = self.kernel.capability.dispatch(call.tool_id, call.arguments)
                tool_results.append(result)
                final = self.after_tool(call.tool_id, result)
        self.kernel.memory.capture(
            MemoryRuntimeStep(
                observation=message,
                memory_view=self.kernel.runtime_state.last_memory_view,
                capability_view=self.kernel.runtime_state.last_surface_snapshot.capability_view if self.kernel.runtime_state.last_surface_snapshot else None,
                reply={"assistant_message": final, "tool_calls": []},
                tool_results=self.kernel.runtime_state.tool_results[-4:],
            )
        )
        return final or "Max steps reached."

    def begin(self, message: str, files: list[dict] | None = None) -> None:
        self.kernel.events.emit("user.turn.started", message=message, attachments=len(files or []))
        ingest = self.kernel.ingest_attachments(files)
        if ingest:
            self.kernel.session.history.append_system(f"Attachment ingest summary:\n{ingest}")
        self.kernel.session.history.append_user(message, files=files)

    def after_tool(self, tool_id: str, result: ToolExecutionResult) -> str:
        normalized = self.kernel.normalizer.normalize_tool_result(tool_id, result.content)
        self.kernel.runtime_state.last_tool_result = normalized
        self.kernel.runtime_state.tool_results.append(normalized)
        self.kernel.session.history.append_tool(tool_id, normalized)
        self.kernel.events.emit("tool.result" if result.ok else "tool.error", tool=tool_id, result=normalized)
        for extension in self.kernel.runtime_state.installed_toolboxes.values():
            hook = getattr(extension, "after_tool_call", None)
            if hook:
                try:
                    hook(tool_id, normalized)
                except Exception:
                    pass
        return normalized
