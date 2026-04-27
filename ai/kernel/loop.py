from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from capability.binding import CapabilityExecutorBinder
from capability.loader import CapabilityClassLoader
from capability.registry import CapabilityRegistry
from capability.runtime import RuntimeCapability
from kernel.audit import AuditLog
from kernel.events import EventBus
from kernel.guard import KernelGuard
from kernel.normalizer import Normalizer, clip_text
from kernel.parser import KernelReplyParser
from kernel.policy import KernelPolicy
from kernel.profile import AgentProfile
from kernel.profile_store import AgentProfileStore
from kernel.prompt import PromptAssembler
from kernel.session import SessionState
from kernel.skill_state import KernelSkillState
from kernel.state import AgentResult, KernelContext, KernelRequest, KernelRuntimeState, KernelSettings, PromptPacket, RuntimeStep
from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from memory import MemoryService
from shared.ids import new_id
from workspace_paths import workspace_root

TOOL_RESULT_ENVELOPE = '<tool_result tool="{tool}">\n{content}\n</tool_result>'


class KernelEngine:
    """Thin public facade over the Memory-Native Kernel."""

    def __init__(self, kernel: "Kernel"):
        self.kernel = kernel

    def chat(self, message: str, files: list[dict] | None = None) -> str:
        return self.kernel.run(message, files=files)

    def tick(self) -> str:
        autonomy = self.kernel.runtime_state.installed_toolboxes.get("autonomy")
        if autonomy is None:
            return "Autonomy not enabled."
        result = autonomy.idle_tick()
        if result and not str(result).startswith("No unclaimed"):
            return self.chat(f"Auto-claimed task detail:\n{result}")
        return str(result)

    def spawn_child(
        self,
        *,
        skill: str | None,
        role_name: str,
        tools: list[str] | None = None,
        enhancements: list[str] | None = None,
        toolboxes: list[str] | None = None,
    ):
        return self.kernel.spawn_child(skill=skill, role_name=role_name, tools=tools, enhancements=enhancements, toolboxes=toolboxes)


class Kernel:
    """Memory-native Observe -> Orient -> Act -> Reflect -> Commit loop."""

    def __init__(
        self,
        *,
        project_root: Path,
        profile: AgentProfile,
        settings: KernelSettings,
        session: SessionState,
        memory: MemoryService,
        capability_registry: CapabilityRegistry,
        capability: RuntimeCapability | None,
        skill_state: KernelSkillState,
        events: EventBus,
        audit: AuditLog,
        guard: KernelGuard,
        runtime_state: KernelRuntimeState,
        normalizer: Normalizer,
        llm: Any,
        context: KernelContext,
        profile_store: AgentProfileStore,
        executor_registry: dict[str, Any] | None = None,
        engine_id: str = "",
    ):
        self.project_root = Path(project_root).resolve()
        self.profile = profile
        self.agent = profile
        self.settings = settings
        self.session = session
        self.memory = memory
        self.capability_registry = capability_registry
        self.capability = capability
        self.skill_state = skill_state
        self.events = events
        self.audit = audit
        self.guard = guard
        self.runtime_state = runtime_state
        self.normalizer = normalizer
        self.llm = llm
        self.context = context
        self.profile_store = profile_store
        self.executor_registry = dict(executor_registry or {})
        self.active_tool_ids: set[str] = set()
        self.prompt = PromptAssembler()
        self.parser = KernelReplyParser()
        self.engine_id = engine_id or context.engine_id

    @classmethod
    def create(cls, request: KernelRequest) -> "Kernel":
        project_root = Path(request.project_root).resolve()
        memory = MemoryService(project_root)
        profile_store = AgentProfileStore(project_root, memory=memory)
        profile = profile_store.load(request.agent_id)
        llm_overrides = dict(profile.llm)
        for key in ("provider", "model", "api_key", "base_url"):
            value = getattr(request, key, None)
            if value is not None:
                llm_overrides[key] = value
        llm_config = resolve_llm_config(
            llm_overrides.get("provider"),
            llm_overrides.get("model"),
            llm_overrides.get("api_key"),
            llm_overrides.get("base_url"),
        )
        policy = profile.policy
        override_policy = dict(request.policy or {})
        settings = KernelSettings(
            provider=llm_config.provider,
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            task_id=request.task_id,
            max_steps=int(override_policy.get("max_steps", request.max_steps or policy.max_steps)),
            max_prompt_chars=int(override_policy.get("max_prompt_chars", policy.max_prompt_chars)),
            tool_permission_level=int(override_policy.get("tool_permission_level", policy.tool_permission_level)),
            allowed_tool_categories=_tuple(override_policy.get("allowed_tool_categories", policy.allowed_tool_categories)),
            denied_tool_categories=_tuple(override_policy.get("denied_tool_categories", policy.denied_tool_categories)),
            allowed_tools=_tuple(override_policy.get("allowed_tools", policy.allowed_tools)),
            denied_tools=_tuple(override_policy.get("denied_tools", policy.denied_tools)),
        )
        storage_root = (request.storage_base or workspace_root(project_root) / ".runtime_data").resolve()
        
        try:
            session = SessionState(settings, storage_root)
        except OSError:
            import tempfile
            session = SessionState(settings, Path(tempfile.gettempdir()) / "mc_design_ai_runtime")
        memory = MemoryService(project_root, session=session)
        capability_registry = CapabilityRegistry(project_root, memory=memory)
        capability_registry.refresh()
        audit = AuditLog()
        events = EventBus()
        guard = KernelGuard(logs_dir=session.paths.logs_dir, audit=audit, events=events)
        skill_state = KernelSkillState(profile_store, profile.root_skill_id, audit)
        engine_id = request.role_name or new_id("kernel")
        context = KernelContext(
            engine_id=engine_id,
            root_skill_id=profile.root_skill_id,
            active_skill_id=skill_state.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=profile.agent_id,
            agent_context=profile.role,
        )
        kernel = cls(
            project_root=project_root,
            profile=profile,
            settings=settings,
            session=session,
            memory=memory,
            capability_registry=capability_registry,
            capability=None,
            skill_state=skill_state,
            events=events,
            audit=audit,
            guard=guard,
            runtime_state=KernelRuntimeState(),
            normalizer=Normalizer(),
            llm=LLMFactory.create(llm_config.provider, llm_config.model, llm_config.api_key, llm_config.base_url),
            context=context,
            profile_store=profile_store,
            engine_id=engine_id,
        )
        kernel._install_capability_executors(request.toolboxes or profile.toolboxes)
        kernel.capability = RuntimeCapability(kernel)
        return kernel

    def run(self, message: str, files: list[dict] | None = None) -> str:
        self.begin(message, files)
        final = ""
        for step in range(self.settings.max_steps):
            self.runtime_state.step = step + 1
            memory_view = self.memory.orient(message, runtime_state=self.runtime_state)
            self.runtime_state.last_memory_view = memory_view
            capability_view = self.capability.orient(observation=message, memory_view=memory_view) if self.capability else None
            self.runtime_state.last_capability_view = capability_view
            self.active_tool_ids = {item.capability_id for item in getattr(capability_view, "visible_tools", [])}
            packet = self.compile_prompt(message, memory_view, capability_view)
            for extension in self.runtime_state.installed_toolboxes.values():
                hook = getattr(extension, "before_model_call", None)
                if hook:
                    try:
                        hook()
                    except Exception:
                        pass
            raw = self.llm.complete(packet.system_prompt, packet.messages)
            reply = self.parser.parse(raw)
            self.audit.record("llm.response", raw=raw, tool_calls=len(reply.tool_calls))
            if reply.assistant_message:
                final = reply.assistant_message
                self.session.history.append_assistant(final)
            if not reply.tool_calls:
                self.memory.capture(RuntimeStep(message, memory_view, capability_view, reply, []))
                self.events.emit("kernel.turn.completed", final_answer=final)
                return final
            tool_results = []
            for call in reply.tool_calls:
                result = self.capability.dispatch(call.tool_id, call.arguments, visible_capability_ids=self.active_tool_ids)
                tool_results.append(result)
                final = self.after_tool(call.tool_id, result)
        self.memory.capture(RuntimeStep(message, self.runtime_state.last_memory_view, self.runtime_state.last_capability_view, {"assistant_message": final, "tool_calls": []}, self.runtime_state.tool_results[-4:]))
        return final or "Max steps reached."

    def begin(self, message: str, files: list[dict] | None = None) -> None:
        self.events.emit("user.turn.started", message=message, attachments=len(files or []))
        for extension in self.runtime_state.installed_toolboxes.values():
            hook = getattr(extension, "before_user_turn", None)
            if hook:
                try:
                    hook(message)
                except Exception:
                    pass
        ingest = self.ingest_attachments(files)
        if ingest:
            self.session.history.append_system(f"Attachment ingest summary:\n{ingest}")
        self.session.history.append_user(message, files=files)

    def after_tool(self, capability_id: str, result) -> str:  # noqa: ANN001
        normalized = self.normalizer.normalize_tool_result(capability_id, result.content)
        self.runtime_state.last_tool_result = normalized
        self.runtime_state.tool_results.append(normalized)
        self.session.history.append_tool(capability_id, normalized)
        self.events.emit("capability.result" if result.ok else "capability.error", capability=capability_id, result=normalized)
        for extension in self.runtime_state.installed_toolboxes.values():
            hook = getattr(extension, "after_tool_call", None)
            if hook:
                try:
                    hook(capability_id, normalized)
                except Exception:
                    pass
        return normalized

    def compile_prompt(self, message: str, memory_view, capability_view) -> PromptPacket:  # noqa: ANN001
        system_prompt = clip_text(
            self.prompt.compile(
                identity={
                    "agent_id": self.profile.agent_id,
                    "engine_id": self.engine_id,
                    "active_skill": self.skill_state.active_skill_id,
                    "root_skill": self.skill_state.root_skill_id,
                    "provider": self.settings.provider,
                    "model": self.settings.model,
                    "max_steps": self.settings.max_steps,
                },
                observation=message,
                memory_view=memory_view,
                capability_view=capability_view,
                runtime_state=self._runtime_state_payload(),
            ),
            limit=self.settings.max_prompt_chars,
        )
        return PromptPacket(system_prompt=system_prompt, messages=self._messages())

    def _messages(self) -> list[dict]:
        rows = self.session.history.read()
        keep = self.settings.history_keep_turns
        messages: list[dict] = []
        for item in rows[-keep:]:
            role = item.get("role")
            content = str(item.get("content") or "")
            if role == "tool":
                messages.append({"role": "user", "content": TOOL_RESULT_ENVELOPE.format(tool=item.get("tool") or item.get("action"), content=content)})
            elif role == "system":
                messages.append({"role": "user", "content": f"<system_note>\n{content}\n</system_note>"})
            else:
                messages.append({"role": role, "content": content})
        return messages

    def _runtime_state_payload(self) -> dict:
        return {
            "step": self.runtime_state.step,
            "tool_results": [clip_text(item, limit=400) for item in self.runtime_state.tool_results[-4:]],
            "state_fragments": self.state_fragments(),
        }

    def state_fragments(self) -> list[str]:
        rows: list[str] = []
        rows.extend(self.memory.state_fragments())
        for extension in self.runtime_state.installed_toolboxes.values():
            hook = getattr(extension, "state_fragments", None)
            if hook:
                try:
                    rows.extend(hook())
                except Exception:
                    pass
        return self.normalizer.normalize_state_fragments(rows)

    def ingest_attachments(self, files: list[dict] | None) -> str | None:
        if not files:
            return None
        return self.memory.ingest(files)

    def policy_payload(self) -> dict:
        return {
            "tool_permission_level": self.settings.tool_permission_level,
            "allowed_tool_categories": list(self.settings.allowed_tool_categories),
            "denied_tool_categories": list(self.settings.denied_tool_categories),
            "allowed_tools": list(self.settings.allowed_tools),
            "denied_tools": list(self.settings.denied_tools),
        }

    def _install_capability_executors(self, requested: list[str]) -> None:
        loader = CapabilityClassLoader(self.project_root)
        classes = loader.discover()
        binder = CapabilityExecutorBinder()
        installed = binder.install_toolboxes(requested=requested, toolbox_classes=classes, workspace_root=self.session.workspace_root, kernel=self)
        self.runtime_state.installed_toolboxes = installed
        self.executor_registry = binder.collect_executors(installed)

    def spawn_child(self, *, skill: str | None, role_name: str, tools: list[str] | None = None, enhancements: list[str] | None = None, toolboxes: list[str] | None = None):
        target_skill = self.skill_state.active_skill_id if skill in (None, "", "root") else self.skill_state.resolve_skill_alias(str(skill))
        request = KernelRequest(
            agent_id=self.profile.agent_id,
            project_root=self.project_root,
            provider=self.settings.provider,
            model=self.settings.model,
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            user_id=self.settings.user_id,
            conversation_id=self.settings.conversation_id,
            task_id=f"{self.settings.task_id}__{role_name}",
            toolboxes=tools or toolboxes or enhancements or list(self.runtime_state.installed_toolboxes),
            storage_base=self.session.paths.root.parents[2],
            role_name=role_name,
            policy={"max_prompt_chars": max(6000, self.settings.max_prompt_chars // 2)},
        )
        child_kernel = Kernel.create(request)
        child_kernel.skill_state.active_skill_id = target_skill
        child_kernel.context.active_skill_id = target_skill
        return KernelEngine(child_kernel)


class KernelService:
    def build(self, request: KernelRequest) -> KernelEngine:
        return KernelEngine(Kernel.create(request))


def build_engine(agent_id: str, *, project_root: Path, **overrides: Any) -> KernelEngine:
    return KernelService().build(KernelRequest(agent_id=agent_id, project_root=Path(project_root), **overrides))


def _tuple(value) -> tuple[str, ...]:  # noqa: ANN001
    if value is None:
        return ()
    if isinstance(value, str):
        if any(ch in value for ch in ",，、"):
            return tuple(item.strip() for item in value.replace("，", ",").replace("、", ",").split(",") if item.strip())
        return (value,)
    return tuple(str(item) for item in value)


class KernelPreviewLoop:
    """Preview-oriented Observe -> Orient -> Act -> Reflect -> Commit skeleton."""

    def __init__(self, *, memory, capability_registry, policy):  # noqa: ANN001
        from capability.surface import CapabilitySurfaceResolver

        self.memory = memory
        self.capability_registry = capability_registry
        self.policy = policy
        self.surface = CapabilitySurfaceResolver(capability_registry)
        self.prompt = PromptAssembler()

    def preview(self, task_brief: str) -> AgentResult:
        from kernel.state import Observation

        observation = Observation(task_brief=task_brief)
        memory_view = self.memory.orient(observation.task_brief)
        capability_view = self.surface.resolve(
            observation=observation.task_brief,
            memory_view=memory_view,
            policy={
                "tool_permission_level": self.policy.tool_permission_level,
                "allowed_tool_categories": list(self.policy.allowed_tool_categories),
                "denied_tool_categories": list(self.policy.denied_tool_categories),
                "allowed_tools": list(self.policy.allowed_tools),
                "denied_tools": list(self.policy.denied_tools),
            },
        )
        prompt = self.prompt.compile(
            identity={"agent_id": self.policy.agent_id, "mode": self.policy.mode, "max_steps": self.policy.max_steps},
            observation=observation.task_brief,
            memory_view=memory_view,
            capability_view=capability_view,
            runtime_state={"step": 0},
        )
        proposal = self.memory.capture(
            {
                "proposal_type": "runtime_hint",
                "source": "preview",
                "observation": observation.task_brief,
                "assistant_message": "preview-only",
                "tool_results": [],
                "memory_view": asdict(memory_view),
                "capability_view": asdict(capability_view),
            }
        )
        return AgentResult(reply=prompt, proposal=proposal, memory_view=memory_view, capability_view=capability_view)
