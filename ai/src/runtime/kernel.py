from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llm.config import resolve_llm_config
from llm.factory import LLMFactory
from protocol.registry import RuntimeRegistry
from protocol.types import AgentSpec
from shared.ids import new_id
from tool.binder import ToolExecutorBinder
from tool.loader import ToolboxClassLoader
from wiki.hub import WikiHub
from .audit import AuditLog
from .dispatcher import ToolDispatcher
from .events import EventBus
from .guard import RuntimeGuard
from .normalizer import Normalizer
from .prompt import PromptCompiler
from .session_state import SessionState
from .state import RuntimeState, SkillState
from .surface import ToolSurface
from .types import EngineContext, EngineSettings, RuntimeRequest


@dataclass(slots=True)
class RuntimeKernel:
    registry: RuntimeRegistry
    agent: AgentSpec
    settings: EngineSettings
    session: SessionState
    context: EngineContext
    wiki: WikiHub
    skill_state: SkillState
    events: EventBus
    audit: AuditLog
    guard: RuntimeGuard
    runtime_state: RuntimeState
    normalizer: Normalizer
    llm: Any
    active_tool_ids: set[str] = field(default_factory=set)
    surface: Any = None
    prompt: Any = None
    dispatcher: Any = None
    engine_id: str = ""

    @classmethod
    def create(cls, request: RuntimeRequest, registry: RuntimeRegistry) -> "RuntimeKernel":
        agent = registry.agent(request.agent_id)
        llm_overrides = dict(agent.llm)
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

        policy = dict(agent.policy or {})
        if request.policy:
            policy.update(request.policy)
        settings = EngineSettings(
            provider=llm_config.provider,
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            task_id=request.task_id,
            max_steps=request.max_steps,
            max_prompt_chars=int(policy.get("max_prompt_chars", 18_000)),
            tool_permission_level=int(policy.get("tool_permission_level", 1)),
            allowed_tool_categories=_tuple(policy.get("allowed_tool_categories", ())),
            denied_tool_categories=_tuple(policy.get("denied_tool_categories", ())),
            allowed_tools=_tuple(policy.get("allowed_tools", ())),
            denied_tools=_tuple(policy.get("denied_tools", ())),
        )
        storage_root = (request.storage_base or registry.project_root / ".runtime_data").resolve()
        session = SessionState(settings, storage_root)
        audit = AuditLog()
        events = EventBus()
        guard = RuntimeGuard(logs_dir=session.paths.logs_dir, audit=audit, events=events)
        skill_state = SkillState(registry, agent.root_skill, audit)
        engine_id = request.role_name or new_id("engine")
        context = EngineContext(
            engine_id=engine_id,
            root_skill_id=agent.root_skill,
            active_skill_id=skill_state.active_skill_id,
            settings=settings,
            paths=session.paths,
            agent_name=agent.agent_id,
            agent_context=agent.context,
        )
        wiki = WikiHub(project_root=registry.project_root, registry=registry, session=session)
        kernel = cls(
            registry=registry,
            agent=agent,
            settings=settings,
            session=session,
            context=context,
            wiki=wiki,
            skill_state=skill_state,
            events=events,
            audit=audit,
            guard=guard,
            runtime_state=RuntimeState(),
            normalizer=Normalizer(),
            llm=LLMFactory.create(llm_config.provider, llm_config.model, llm_config.api_key, llm_config.base_url),
            engine_id=engine_id,
        )
        kernel._install_toolboxes(request.toolboxes or agent.installation_names())
        kernel.surface = ToolSurface(kernel)
        kernel.prompt = PromptCompiler(kernel)
        kernel.dispatcher = ToolDispatcher(kernel)
        return kernel

    def _install_toolboxes(self, requested: list[str]) -> None:
        loader = ToolboxClassLoader()
        classes = loader.discover()
        binder = ToolExecutorBinder()
        installed = binder.install_toolboxes(
            requested=requested,
            toolbox_classes=classes,
            workspace_root=self.session.workspace_root,
            runtime=self,
        )
        self.runtime_state.installed_toolboxes = installed
        self.runtime_state.tool_registry = binder.bind(self.registry.tools, installed)

    def state_fragments(self) -> list[str]:
        rows: list[str] = []
        rows.extend(self.wiki.state_fragments())
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
        return self.wiki.ingest_user_files(files)


def _tuple(value) -> tuple[str, ...]:  # noqa: ANN001
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)
