from __future__ import annotations

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
            surface = self.kernel.surface.resolve()
            packet = self.kernel.prompt.compile(surface)
            raw = self.kernel.llm.complete(packet.system_prompt, packet.messages)
            reply = self.parser.parse(raw)
            self.kernel.audit.record("llm.response", raw=raw, tool_calls=len(reply.tool_calls))
            if reply.assistant_message:
                final = reply.assistant_message
                self.kernel.session.history.append_assistant(final)
            if not reply.tool_calls:
                self.kernel.events.emit("model.turn.completed", final_answer=final)
                return final
            for call in reply.tool_calls:
                result = self.kernel.dispatcher.dispatch(call.tool_id, call.arguments)
                final = self.after_tool(call.tool_id, result)
        return final or "Max steps reached."

    def begin(self, message: str, files: list[dict] | None = None) -> None:
        self.kernel.events.emit("user.turn.started", message=message, attachments=len(files or []))
        ingest = self.kernel.ingest_attachments(files)
        if ingest:
            self.kernel.session.history.append_system(f"Attachment ingest summary:\n{ingest}")
        self.kernel.session.history.append_user(message, files=files)

    def after_tool(self, tool_id: str, result: ToolExecutionResult) -> str:
        normalized = self.kernel.normalizer.normalize_tool_result(tool_id, result.content)
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
