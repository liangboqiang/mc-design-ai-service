Memory-Native Agent Kernel 设计改造蓝图
============================================================

版本：v1.0
对象仓库：liangboqiang/mc-design-ai-service main 分支
目标：基于当前仓库现状，设计一套完全重构后的通用知识增强 Agent 架构。
关键变化：不再以 wiki.md 为中心；统一改为 note.md；不再把 Wiki 作为外挂知识库接入 Engine，而是将 Knowledge/Wiki/Graph/Context 全部归入 Agent 原生 Memory 层。

============================================================
0. 当前 main 分支现状概述
============================================================

0.1 当前应用形态

当前 main 分支是一个单仓、单端口、前端内联构建、后端 Starlette 直连函数的 Wiki Workbench 应用。

运行链路是：

browser
  -> /app/wiki/action/{action}
  -> main_app.py
  -> ai/wiki_app/actions.py
  -> ai/wiki_app/service.py
  -> WikiHub / WikiWorkbench / user_files

启动入口是 __main__.py：
- 自动将项目根目录、ai、ai/src 加入 sys.path；
- 检查 web/dist 是否过期；
- 必要时执行 scripts.build_web.build()；
- 支持 --check；
- 最后 uvicorn 启动 main_app:app。

Web 入口是 main_app.py：
- 使用 Starlette；
- 暴露 /health、/app-config.json、/app/diagnostics、/app/wiki/actions、/app/wiki/action/{action}；
- 静态资源和 SPA fallback 由同一个服务承载；
- 前端所有动作最终进入 WikiAppActionRouter。

当前 Action 层是 ai/wiki_app/actions.py：
- 通过一个大 ACTIONS 字典注册所有 action；
- 每个 ActionSpec 包含 name、method、required、defaults、description；
- dispatch 时做参数合并和必填校验；
- 通过 getattr(self.service, spec.method) 调用 WikiAppService。

当前 Service 层是 ai/wiki_app/service.py：
- WikiAppService 同时持有 WikiHub、WikiWorkbench、WikiAppSessionManager；
- 承担搜索、读页、问答、草稿、发布、版本、schema、图谱、诊断、后台、用户文件等大量职能；
- 本质上是“Web UI 的应用服务巨石”。

当前 Runtime 层：
- RuntimeKernel 直接创建 WikiHub，并将 wiki 注入 kernel；
- TurnLoop 只负责 begin -> surface.resolve -> prompt.compile -> llm.complete -> parser -> dispatcher -> after_tool；
- PromptCompiler 直接拼 Agent Wiki、Active Skill Wiki、Visible Skills、Visible Tools、Wiki Hub、Runtime State、Response Contract；
- ToolSurface 直接根据 Skill 引用、工具权限、类别、激活规则决定可见工具。

当前 Wiki / Protocol 层：
- WikiAdapterBridge 扫描 src/**/*.md；
- 如果文件名是 wiki.md，则 node_id 使用其相对目录；
- 根据路径推断 kind，如 agent、skill、tool、toolbox、knowledge；
- 从 Markdown 中解析标题、section、links、runtime block；
- ProtocolCompiler 从 WikiAdapterBridge 获取 WikiNode，编译成 AgentSpec、SkillSpec、ToolSpec、ToolboxSpec；
- RuntimeRegistry 消费 ProtocolView。

当前图谱层：
- WikiGraphService.extract_knowledge_graph() 遍历 catalog；
- 读取页面 Markdown；
- parse_chinese_page；
- 将实体类型、作用范围、链接、局部关系、所属工具箱等写为 triples；
- 当前图谱实际上混合了属性、弱引用、局部语义关系、路径关系、运行关系，导致图谱语义混乱。

当前前端层：
- scripts/build_web.py 只内联 web/src/assets/style.css 和 app.js；
- app.js 是单文件 SPA，承载首页、搜索、详情、图谱、后台、用户中心等全部页面；
- 前端和后端通过 /app/wiki/action/{action} 通信。

0.2 当前架构的核心问题

当前系统的问题不是“Wiki 做得不够好”，而是 Wiki 链路已经反向侵入了通用 Agent Engine：

1. RuntimeKernel 直接持有 WikiHub。
   Engine 内核开始知道 Wiki 的存在。

2. PromptCompiler 直接拼 Agent Wiki、Active Skill Wiki、Wiki Hub。
   Prompt 层被 Wiki 语义污染。

3. ProtocolCompiler 从 Wiki 页面直接编译 AgentSpec / SkillSpec / ToolSpec。
   Wiki 既是文档，又是运行协议，又是配置源。

4. GraphService 直接从 Markdown 中生成 triples。
   属性、关系、弱链接、运行事实混杂。

5. WikiAppService 作为应用服务层过重。
   它同时承载 Web action、WikiHub、Workbench、图谱、诊断、用户文件等。

6. app.js 单文件前端膨胀。
   页面职责、交互逻辑、状态管理、API client 混合在一起。

因此，如果继续在当前 Wiki 架构上打补丁，系统会越来越复杂。需要从“Agent 架构本体”重新设计，使知识系统天然成为 Agent 原生 Memory，而不是外接 Wiki。

============================================================
1. 新架构总定义
============================================================

新架构名称：

Memory-Native Agent Kernel

一句话定义：

以 Kernel 负责通用智能体运行循环；
以 Memory 统一承载源文件、note.md、Lens、图谱、上下文视图和候选补丁；
以 Capability 统一承载 Skill、Tool、Workflow、MCP 和外部执行能力；
以 Workbench 统一承载导入、审核、诊断、发布、回滚、图谱和运行预览。

最终一级模块只保留四个：

1. Kernel
2. Memory
3. Capability
4. Workbench

Transport / App 只作为外部接口层，不是核心架构层。

============================================================
2. 核心架构图
============================================================

                         ┌────────────────────────────┐
                         │         Workbench          │
                         │ 导入 / 审核 / 诊断 / 发布  │
                         │ 图谱 / 运行预览 / 测试      │
                         └──────────────┬─────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                              Memory                              │
│                                                                  │
│  Evidence -> note.md -> Lens -> Index -> MemoryView              │
│                                                                  │
│  EvidenceStore   原始证据                                        │
│  NoteStore       note.md 管理                                    │
│  Lens            轻解释规则                                      │
│  Index           SearchIndex / MemoryGraph / StatusIndex         │
│  Orienter        生成当前任务 MemoryView                         │
│  Curator         LLM 辅助抽取、补全、诊断                         │
│  ProposalQueue   候选修改和审核队列                              │
└──────────────────────────────┬───────────────────────────────────┘
                               │ MemoryView / ActivationHints
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                              Kernel                              │
│                                                                  │
│        Observe -> Orient -> Act -> Reflect -> Commit             │
│                                                                  │
│  Kernel 不读 note.md，不解析 Lens，不直接读 Graph。               │
│  Kernel 只消费 MemoryView、CapabilityView、RuntimeState。         │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                            Capability                            │
│                                                                  │
│  Skill / Tool / Workflow / MCP / External API / Script / DB / NX  │
│                                                                  │
│  CapabilityRegistry                                              │
│  CapabilitySpec                                                  │
│  SurfaceResolver                                                 │
│  Dispatcher                                                      │
└──────────────────────────────────────────────────────────────────┘

关键边界：

- Kernel 不读 note.md，只读 MemoryView。
- Capability 不读 note.md，只读 CapabilitySpec / CapabilityView。
- Graph 不是真相，只是 Memory 的关系索引。
- Context 不是独立工程，只是 MemoryView。
- Lens 不是治理系统，只是 note.md 的解释镜头。
- Workbench 不进入 runtime loop，只审核 Proposal。
- LLM 不是裁判，只是 Curator 能力来源。

============================================================
3. 新旧概念映射
============================================================

当前概念                         新架构定位
------------------------------------------------------------
wiki.md                          note.md，MemoryNote 的存储格式
WikiHub                          Memory 的 NoteStore + Index + Search 兼容门面
WikiWorkbench                    Workbench Facade，逐步拆到 Workbench 模块
WikiGraphService                 MemoryGraphProjector / GraphIndex
WikiSchemaService                LensService / NoteDiagnosis
ProtocolCompiler                 CapabilityProjector + RuntimeProjection
RuntimeRegistry                  CapabilityRegistry + RuntimeCatalog
AgentSpec                        Kernel Policy / AgentProfile / CapabilityScope 投影
SkillSpec                        CapabilitySpec 或 MemoryNote 投影
ToolSpec                         CapabilitySpec
PromptCompiler                   Kernel PromptAssembler，只拼 MemoryView 和 CapabilityView
ToolSurface                      Capability SurfaceResolver
WikiAppActionRouter              App ActionRouter，短期兼容；长期改为 WorkbenchActionRouter
src/wiki/store/*.json            data/indexes/*.json，派生产物
src/wiki/workbench/store/drafts  data/proposals 或 data/workbench/drafts
user_files                       EvidenceStore 的一种来源目录

============================================================
4. 核心对象定义
============================================================

4.1 Evidence

Evidence 是原始证据，不是知识本身。

包括：
- 代码文件；
- 用户上传 PDF / Word / Excel；
- 系统配置；
- 历史报告；
- 工具输出；
- 旧版 Markdown；
- 自动扫描结果。

Evidence 不直接进入 Prompt，不直接成为图谱关系，不直接驱动 Runtime。

建议结构：

@dataclass
class EvidenceRecord:
    evidence_id: str
    source_kind: str              # code | upload | tool_result | config | legacy_note
    uri: str
    title: str
    hash: str
    created_at: str
    metadata: dict
    extracted_text_path: str | None
    linked_note_ids: list[str]

4.2 MemoryNote

MemoryNote 是系统与人共同维护的知识单元。

note.md 是 MemoryNote 的人机可读存储格式。

@dataclass
class MemoryNote:
    note_id: str
    title: str
    kind: str                     # Agent | Skill | Tool | Rule | Document | Case | Part | Policy
    status: str                   # raw | draft | reviewed | published | projectable | runtime_ready | locked | deprecated
    body: str
    fields: dict
    relations: list[RelationHint]
    source_refs: list[str]
    tags: list[str]
    maturity: str
    path: str

4.3 Lens

Lens 是 Soft Schema 的新定位。不要再叫 Schema 中心，建议叫 Lens，即“解释镜头”。

Lens 不强制 note 一开始完整，只定义推荐字段、关系提示、投影提示和成熟度检查。

@dataclass
class Lens:
    lens_id: str
    applies_to: list[str]         # kind 列表
    suggested_fields: dict
    relation_hints: dict
    projection_hints: dict
    maturity_checks: dict

4.4 MemoryGraph

MemoryGraph 是 Memory 的关系索引，不是真相。

边的来源只保留四类：
- declared：来自 note 显式字段或 Relations 块；
- linked：来自正文链接；
- inferred：来自 LLM 候选；
- runtime：来自执行日志、工具调用事实、运行时绑定事实。

边的状态：
- candidate
- reviewed
- published
- rejected

@dataclass
class MemoryEdge:
    edge_id: str
    source: str
    target: str
    predicate: str
    label: str
    kind: str
    status: str
    confidence: float
    evidence: str
    source_note: str
    source_field: str | None

4.5 MemoryView

MemoryView 是当前任务的知识视图。它替代“上下文工程”。

@dataclass
class MemoryView:
    task_brief: str
    system_cards: list[MemoryCard]
    business_cards: list[MemoryCard]
    constraints: list[str]
    relations: list[MemoryEdge]
    unknowns: list[str]
    activation_hints: list[ActivationHint]
    citations: list[EvidenceRef]
    diagnostics: list[Diagnostic]

4.6 CapabilitySpec

CapabilitySpec 是机器可执行能力定义，不等于 note.md。

@dataclass
class CapabilitySpec:
    capability_id: str
    kind: str                     # Skill | Tool | Workflow | MCP
    title: str
    description: str
    input_schema: dict
    output_schema: dict
    permission_level: int
    categories: list[str]
    executor_ref: str | None
    safety: str
    source_note_id: str | None

4.7 CapabilityView

CapabilityView 是当前回合可见能力视图。

@dataclass
class CapabilityView:
    visible_skills: list[CapabilitySpec]
    visible_tools: list[CapabilitySpec]
    visible_workflows: list[CapabilitySpec]
    activation_reasons: list[str]
    denied_reasons: list[str]

4.8 Proposal

Proposal 是系统中所有不确定变化的统一容器。

@dataclass
class Proposal:
    proposal_id: str
    proposal_type: str            # note_create | note_patch | edge_add | lens_patch | runtime_hint
    status: str                   # candidate | reviewed | accepted | rejected | applied
    source: str                   # llm | user | runtime | import
    payload: dict
    evidence_refs: list[str]
    created_at: str
    review_notes: str

============================================================
5. note.md 规范
============================================================

5.1 文件命名

从现在开始，新体系统一采用 note.md。

短期兼容：
- 继续读取旧 wiki.md；
- 新建页面一律使用 note.md；
- 如果同目录下同时存在 note.md 和 wiki.md，优先 note.md；
- 编译器给 wiki.md 产生 deprecation warning；
- 最终迁移完成后删除 wiki.md 支持。

5.2 note.md 最小格式

---
id: agent.part_design
kind: Agent
status: draft
maturity: projectable
lens: lens.agent
source_refs:
  - evidence.system.agent_doc
tags:
  - design
  - part
---

# 零部件设计智能体

## Summary

用于处理零部件设计任务，包括需求澄清、参数化建模、工具调用和报告生成。

## Fields

- 角色定位：零部件设计任务的主控智能体
- 推荐技能：[[skill.parametric_modeling]], [[skill.part_retrieval]]
- 推荐工具：[[tool.nx_modeling]]
- 适用对象：连杆、曲轴、凸轮轴

## Relations

- uses: [[skill.parametric_modeling]]
- uses: [[skill.part_retrieval]]
- can_activate: [[tool.nx_modeling]]

## Runtime Notes

达到 runtime_ready 后，可投影为 AgentProfile、Policy、CapabilityScope。

## Evidence

- 来源：系统设计文档
- 审核人：待补充

5.3 note.md 编写原则

1. note 可以半结构化。
2. note 可以缺字段。
3. note 可以先由 LLM 生成 draft。
4. note 的 Relations 可以为空。
5. note 进入 published 前必须人工审核。
6. note 进入 projectable 前必须能生成 MemoryView。
7. note 进入 runtime_ready 前必须能投影为运行结构。

============================================================
6. 成熟度模型
============================================================

所有系统知识和业务知识共用同一个成熟度模型。

raw
  -> draft
  -> reviewed
  -> published
  -> projectable
  -> runtime_ready
  -> locked / deprecated

含义：

raw:
  只有 Evidence，没有稳定 note。

draft:
  已生成 note 草稿，可以编辑，可以诊断。

reviewed:
  人已审核内容，但未发布。

published:
  可以被搜索、阅读、图谱展示。

projectable:
  可以进入 MemoryView、MemoryGraph、SearchIndex。

runtime_ready:
  可以投影为 AgentProfile、CapabilitySpec、Policy、ToolSurface 输入。

locked:
  锁定，不允许 LLM 自动 patch。

deprecated:
  废弃，默认不参与检索、图谱和 Runtime。

关键原则：

- 系统知识和业务知识不再使用两套治理规则。
- 越靠近运行时，成熟度门槛越高。
- 所有 note 都允许缺字段，但 runtime_ready 不允许缺关键运行字段。

============================================================
7. Kernel 设计
============================================================

7.1 Kernel 的定位

Kernel 是通用智能体内核，只负责执行循环。

它不负责：
- 解析 note.md；
- 构建图谱；
- 管理 Lens；
- 扫描文件；
- 审核知识；
- 直接理解 Skill note 或 Tool note。

它只负责：
- 接收 Observation；
- 请求 MemoryView；
- 请求 CapabilityView；
- 组织 Prompt；
- 调用模型；
- 调用 Dispatcher；
- 反思结果；
- 提交 Proposal。

7.2 Kernel Loop

Observe
  -> Orient
  -> Act
  -> Reflect
  -> Commit

伪代码：

class Kernel:
    def run(self, observation: Observation) -> AgentResult:
        self.event_bus.emit("turn.started", observation=observation)

        memory_view = self.memory.orient(observation, self.policy)

        capability_view = self.capability.orient(
            observation=observation,
            memory_view=memory_view,
            policy=self.policy,
        )

        for step in range(self.policy.max_steps):
            prompt = self.prompt.compile(
                observation=observation,
                memory_view=memory_view,
                capability_view=capability_view,
                runtime_state=self.state,
            )

            reply = self.llm.complete(prompt)

            parsed = self.parser.parse(reply)

            if not parsed.tool_calls:
                proposal = self.memory.capture(
                    RuntimeStep(
                        observation=observation,
                        memory_view=memory_view,
                        capability_view=capability_view,
                        reply=parsed,
                        tool_results=[],
                    )
                )
                return AgentResult(reply=parsed.assistant_message, proposal=proposal)

            results = []
            for call in parsed.tool_calls:
                results.append(self.capability.dispatch(call))

            self.state.append_tool_results(results)

            reflect = self.reflect(observation, parsed, results)
            if reflect.need_reorient:
                memory_view = self.memory.orient(observation, self.policy, runtime_state=self.state)
                capability_view = self.capability.orient(observation, memory_view, self.policy)

        return AgentResult(reply="Max steps reached.", proposal=None)

7.3 Prompt 极简结构

PromptCompiler 只拼六段：

1. Identity
2. Task
3. MemoryView
4. CapabilityView
5. RuntimeState
6. ResponseContract

不再直接出现：
- Agent Wiki；
- Active Skill Wiki；
- Wiki Hub；
- Raw Graph；
- Raw Schema；
- 原始 note.md。

示例：

## Identity
- agent_id: agent.part_design
- mode: design_execution
- max_steps: 8

## Task
用户希望完成连杆参数化设计任务。

## MemoryView
- 相关系统能力：参数化建模 Skill、NX Tool
- 相关业务资料：连杆设计规范、参数范围表
- 关键约束：材料、尺寸、强度、工艺边界
- 未知项：缺少目标工况

## CapabilityView
- skill.parametric_modeling
- tool.nx_modeling
- tool.report_generator

## RuntimeState
- step: 2
- last_tool_result: ...

## ResponseContract
返回严格 JSON：
{
  "assistant_message": "string",
  "tool_calls": [{"tool": "tool.id", "arguments": {}}],
  "memory_requests": [],
  "proposal_hints": []
}

============================================================
8. Memory 设计
============================================================

8.1 Memory 的定位

Memory 是 Agent 的原生状态层，不是外接知识库。

Memory 内部统一管理：
- Evidence；
- note.md；
- Lens；
- SearchIndex；
- MemoryGraph；
- MemoryView；
- Proposal；
- Release。

8.2 Memory 模块结构

ai/memory/
  __init__.py
  types.py
  evidence.py
  note.py
  store.py
  lens.py
  index.py
  graph.py
  orient.py
  curator.py
  proposal.py
  release.py
  diagnostics.py

8.3 Memory 接口

class Memory:
    def ingest(self, source: SourceRef) -> IngestResult:
        ...

    def orient(self, observation: Observation, policy: Policy, runtime_state: RuntimeState | None = None) -> MemoryView:
        ...

    def capture(self, step: RuntimeStep) -> ProposalBatch:
        ...

    def project(self, note_ids: list[str], target: str) -> Projection:
        ...

    def search(self, query: str, policy: SearchPolicy) -> SearchResult:
        ...

    def graph(self, policy: GraphPolicy) -> MemoryGraph:
        ...

8.4 Memory.orient() 的内部流程

Observation
  -> Query Understanding
  -> SearchIndex 检索 note
  -> MemoryGraph 扩展 1-2 跳
  -> Lens projection 过滤字段
  -> Curator 摘要压缩
  -> 生成 MemoryView
  -> 生成 ActivationHints
  -> 返回 Kernel

8.5 Memory.capture() 的内部流程

RuntimeStep
  -> 提取工具结果中的证据
  -> 提取用户确认信息
  -> 生成候选 note patch
  -> 生成候选关系
  -> 生成诊断
  -> 写入 ProposalQueue
  -> 等待 Workbench 审核

============================================================
9. Capability 设计
============================================================

9.1 Capability 的定位

Capability 统一承载系统“能做什么”。

包括：
- Skill；
- Tool；
- Workflow；
- MCP；
- 外部 API；
- Python executor；
- 数据库工具；
- NX 工具；
- 文件工具。

Skill 和 Tool 可以有 note.md 描述，但运行时不直接读取 note.md。

9.2 Capability 模块结构

ai/capability/
  __init__.py
  types.py
  spec.py
  registry.py
  projector.py
  surface.py
  dispatcher.py
  adapters/
    builtin/
    mcp/
    nx/
    database/
    filesystem/

9.3 Capability 接口

class Capability:
    def orient(
        self,
        observation: Observation,
        memory_view: MemoryView,
        policy: Policy,
    ) -> CapabilityView:
        ...

    def dispatch(self, call: ToolCall) -> ToolResult:
        ...

9.4 SurfaceResolver 逻辑

当前 ToolSurface 的逻辑可以保留思想，但改名和边界：

输入：
- observation；
- memory_view.activation_hints；
- policy；
- capability registry；
- permission；
- categories；
- runtime risk level。

输出：
- CapabilityView。

可见能力判断：

visible = installed
      and policy_allowed
      and permission_passed
      and category_allowed
      and (
            activation_mode == "always"
            or requested_by_memory_hint
            or requested_by_active_skill
            or manually_enabled
          )

区别：
- 当前是 Skill -> Tool；
- 新架构是 MemoryView + Policy + SkillScope -> CapabilityView。

============================================================
10. Workbench 设计
============================================================

10.1 Workbench 定位

Workbench 是 Memory-Native Agent 的人机控制台，不是单纯 Wiki 前端。

只处理人必须参与的内容：
- 导入；
- 草稿；
- 候选字段；
- 候选关系；
- 冲突；
- 诊断；
- 发布；
- 回滚；
- 图谱视图；
- Runtime 预览；
- 测试。

10.2 Workbench 页面

1. Intake 导入中心
   - 上传文件；
   - 扫描代码；
   - 生成 Evidence；
   - 生成 note draft。

2. Notes 笔记中心
   - 浏览 note；
   - 编辑 note；
   - 查看来源；
   - 查看成熟度；
   - 查看 Lens 诊断。

3. Review 审核中心
   - 审核 Proposal；
   - 接受 / 拒绝字段候选；
   - 接受 / 拒绝关系候选；
   - 解决冲突；
   - 发布 note。

4. Graph 关系中心
   - declared / linked / inferred / runtime 关系；
   - 关系过滤；
   - 节点详情；
   - 孤立 note；
   - 冲突边；
   - 跳转 note 详情。

5. Runtime 运行预览
   - 输入一个任务；
   - 展示 MemoryView；
   - 展示 CapabilityView；
   - 展示最终 Prompt 预览；
   - 展示 runtime_ready 缺失项；
   - 展示为什么某个工具被激活或隐藏。

6. Tests 测试中心
   - 固定任务集；
   - 检查 MemoryView 是否合理；
   - 检查 Capability 激活是否合理；
   - 检查 Agent 成功率；
   - 回归测试。

10.3 Workbench API

建议新 action 命名：

memory_ingest_source
memory_list_notes
memory_read_note
memory_save_note_draft
memory_check_note
memory_publish_note
memory_list_proposals
memory_review_proposal
memory_compile_indexes
memory_graph_view
memory_preview_runtime
memory_run_test_case

短期保留现有 wiki_* action，做兼容转发。

============================================================
11. 图谱重构设计
============================================================

11.1 当前问题

当前 GraphService 把以下内容都塞成 triples：
- 实体类型；
- 作用范围；
- 链接到；
- 局部关系；
- 属于工具箱。

这导致：
- 属性被当作关系；
- 弱链接和强关系混合；
- LLM 候选和人工确认关系混合；
- 系统运行关系和文档引用关系混合；
- 前端显示必然混乱。

11.2 新 MemoryGraph 原则

Graph = Memory Index，不是真相。

节点来自 note。
边来自四类来源：

declared:
  note.md Fields / Relations 明确声明。

linked:
  正文 [[xxx]] 链接。

inferred:
  Curator / LLM 生成候选。

runtime:
  Kernel / Capability 执行事实。

11.3 边结构

{
  "edge_id": "edge.agent.part_design.uses.skill.parametric_modeling",
  "source": "agent.part_design",
  "target": "skill.parametric_modeling",
  "predicate": "uses",
  "label": "使用",
  "kind": "declared",
  "status": "published",
  "confidence": 1.0,
  "evidence": "Relations: uses [[skill.parametric_modeling]]",
  "source_note": "agent.part_design",
  "source_field": "Relations.uses"
}

11.4 默认显示策略

前端默认显示：
- declared + published；
- runtime + published；
- inferred + reviewed。

默认隐藏：
- linked；
- candidate；
- rejected；
- weak inferred。

11.5 图谱构建流程

NoteStore
  -> NoteParser
  -> LensInterpreter
  -> DeclaredEdgeExtractor
  -> LinkedEdgeExtractor
  -> RuntimeEdgeCollector
  -> InferredEdgeCandidateLoader
  -> EdgeDeduplicator
  -> GraphDiagnostics
  -> MemoryGraph

11.6 图谱诊断

必须输出：

- 孤立 note；
- 缺目标 note 的关系；
- 重复边；
- 冲突关系；
- candidate 未审核；
- runtime_ready note 缺 declared 关系；
- Tool note 没有 CapabilitySpec；
- Agent note 没有 Policy / CapabilityScope；
- 业务 note 没有 source evidence。

============================================================
12. Lens 设计
============================================================

12.1 Lens 不是 Schema 中心

Lens 是解释镜头，不是强模板。

它定义：
- 推荐字段；
- 字段归一化；
- 关系映射；
- MemoryView 投影；
- CapabilityView 投影；
- runtime_ready 检查。

12.2 lens.agent.yaml 示例

id: lens.agent
applies_to:
  - Agent

suggested_fields:
  role:
    aliases: ["角色定位", "智能体使命", "定位"]
  input:
    aliases: ["输入", "入参", "输入说明"]
  output:
    aliases: ["输出", "出参", "输出说明"]
  skills:
    aliases: ["推荐技能", "可用技能", "使用技能"]
    kind: link_list
    target_kind: Skill
  tools:
    aliases: ["推荐工具", "可用工具"]
    kind: link_list
    target_kind: Tool

relation_hints:
  skills:
    predicate: uses
    target_kind: Skill
    kind: declared
  tools:
    predicate: can_activate
    target_kind: Tool
    kind: declared

projection_hints:
  memory_view:
    include:
      - role
      - input
      - output
  runtime:
    include:
      - skills
      - tools
      - policy

maturity_checks:
  published:
    recommended:
      - role
  projectable:
    required_any:
      - summary
      - role
  runtime_ready:
    required:
      - role
      - skills

12.3 Lens 缺字段处理

缺字段不阻塞 draft / published。
缺 runtime 字段只阻塞 runtime_ready。

============================================================
13. 目录重构蓝图
============================================================

13.1 代码目录

ai/
  kernel/
    __init__.py
    loop.py
    state.py
    policy.py
    prompt.py
    parser.py
    events.py
    audit.py

  memory/
    __init__.py
    types.py
    evidence.py
    note.py
    store.py
    lens.py
    index.py
    graph.py
    orient.py
    curator.py
    proposal.py
    release.py
    diagnostics.py
    compat_wiki.py

  capability/
    __init__.py
    types.py
    spec.py
    registry.py
    projector.py
    surface.py
    dispatcher.py
    adapters/
      builtin/
      mcp/
      nx/
      database/
      filesystem/

  workbench/
    __init__.py
    intake.py
    note_service.py
    review.py
    release.py
    diagnosis.py
    preview.py
    graph_service.py
    test_service.py

  app/
    __init__.py
    api.py
    actions.py
    web.py
    diagnostics.py

  legacy/
    wiki_app/
    wiki/
    protocol/

13.2 数据目录

data/
  evidence/
    uploads/
    code/
    tool_results/
    extracted_text/

  notes/
    system/
      agent/
      skill/
      tool/
      policy/
      lens/
    business/
      part/
      rule/
      document/
      case/
      parameter/

  lenses/
    default.lens.yaml
    agent.lens.yaml
    skill.lens.yaml
    tool.lens.yaml
    business_doc.lens.yaml
    part.lens.yaml

  indexes/
    catalog.json
    search.json
    graph.json
    status.json
    embeddings/

  proposals/
    candidate/
    reviewed/
    accepted/
    rejected/

  releases/
    release_manifest.json
    snapshots/

  runtime/
    sessions/
    audit/
    logs/
    state/

13.3 兼容层

短期不要一次性删旧目录。

保留：
- ai/src/wiki/*
- ai/wiki_app/*
- ai/src/protocol/*

但新增：
- ai/memory/compat_wiki.py
- ai/workbench/compat_actions.py

兼容策略：
- 现有 wiki_* action 继续工作；
- 内部逐步转发到 memory_*；
- 最终前端改用 memory_*；
- 最终旧 wiki_* 只保留只读兼容。

============================================================
14. 分阶段改造计划
============================================================

Phase 0：稳定当前 main，冻结旧接口
------------------------------------------------------------

目标：
- 不继续在旧 WikiGraphService / WikiAppService 中扩展新复杂功能；
- 只允许 bug fix；
- 建立新架构目录和基础类型。

动作：
1. 新建 ai/kernel、ai/memory、ai/capability、ai/workbench、ai/app 目录。
2. 新建 ai/memory/types.py，定义 EvidenceRecord、MemoryNote、Lens、MemoryEdge、MemoryView、Proposal。
3. 新建 ai/capability/types.py，定义 CapabilitySpec、CapabilityView。
4. 新建 ai/kernel/state.py，定义 Observation、RuntimeStep、AgentResult。
5. 不动现有运行链路。

验收：
- python __main__.py --check 仍通过；
- 新模块可 import；
- 旧页面可用。

Phase 1：NoteStore 与 note.md 兼容读取
------------------------------------------------------------

目标：
- 引入 note.md；
- 同时兼容旧 wiki.md；
- 不破坏当前 WikiAdapterBridge。

动作：
1. 实现 NoteStore：
   - 扫描 data/notes/**/*.md；
   - 扫描 ai/src/**/note.md；
   - 兼容扫描 ai/src/**/wiki.md；
   - note.md 优先级高于 wiki.md。
2. 实现 NoteParser：
   - frontmatter；
   - title；
   - Summary；
   - Fields；
   - Relations；
   - Evidence；
   - 正文 links。
3. 实现 WikiCompatImporter：
   - 将旧 WikiNode 转为 MemoryNote。
4. 新建 action：
   - memory_list_notes
   - memory_read_note
   - memory_check_note

验收：
- 当前仓库所有 wiki.md 能被识别为 MemoryNote；
- 新建 note.md 能被识别；
- 输出 catalog 不少于当前 WikiHub catalog 数量。

Phase 2：Lens 与轻诊断
------------------------------------------------------------

目标：
- Soft Schema 从旧 schema_service 中抽离为 Lens；
- 缺字段变诊断，不再作为强错误。

动作：
1. 实现 LensStore。
2. 实现 default.lens.yaml。
3. 实现 Agent / Skill / Tool 基础 Lens。
4. 实现 LensInterpreter：
   - 字段别名归一；
   - 推荐字段诊断；
   - runtime_ready 检查。
5. 新建 action：
   - memory_list_lenses
   - memory_check_note
   - memory_check_runtime_ready

验收：
- Agent / Skill / Tool 类型 note 能输出 maturity diagnosis；
- 缺字段不阻塞 published；
- 缺关键运行字段阻塞 runtime_ready。

Phase 3：MemoryGraph 重构
------------------------------------------------------------

目标：
- 替换当前 triples 混杂图谱；
- 输出 nodes + edges + diagnostics；
- triples 仅作为兼容字段。

动作：
1. 新建 ai/memory/graph.py。
2. 实现四类边：
   - declared；
   - linked；
   - inferred；
   - runtime。
3. 实现 EdgeDeduplicator。
4. 实现 GraphDiagnostics。
5. 新建 action：
   - memory_compile_graph
   - memory_graph_view
   - memory_graph_neighbors
6. 旧 wiki_extract_knowledge_graph 转发到 memory_graph_view，并保持兼容输出。

验收：
- Graph JSON 包含 nodes、edges、triples、diagnostics；
- edges 均有 kind/status/evidence；
- 前端默认展示 declared/runtime/reviewed inferred；
- 图谱不再把“实体类型”“作用范围”作为普通边显示。

Phase 4：MemoryView 替代上下文工程
------------------------------------------------------------

目标：
- Context 不再是独立工程；
- Kernel 只消费 MemoryView。

动作：
1. 实现 MemoryOrienter：
   - query 检索；
   - note 召回；
   - graph 扩展；
   - Lens 投影；
   - 摘要压缩；
   - activation_hints。
2. 新建 action：
   - memory_preview_view
3. Workbench 新增 Runtime Preview 页面第一版。

验收：
- 输入任务文本，可以看到 MemoryView；
- MemoryView 明确区分 system_cards、business_cards、relations、activation_hints；
- PromptCompiler 可以试验性使用 MemoryView。

Phase 5：CapabilityView 替换 ToolSurface 直接逻辑
------------------------------------------------------------

目标：
- Skill/Tool 激活从旧 ToolSurface 迁移到 Capability Surface。

动作：
1. 实现 CapabilityRegistry。
2. 实现 CapabilityProjector：
   - 从 runtime_ready note 生成 CapabilitySpec；
   - 兼容旧 ProtocolView ToolSpec。
3. 实现 SurfaceResolver：
   - 输入 Observation + MemoryView + Policy；
   - 输出 CapabilityView。
4. ToolSurface 改为兼容包装，内部调用 Capability.orient。

验收：
- 旧工具仍可见；
- CapabilityView 能解释每个工具为什么可见/不可见；
- activation_hints 能影响工具可见性，但不能绕过权限。

Phase 6：Kernel 重构
------------------------------------------------------------

目标：
- RuntimeKernel 不再直接持有 WikiHub；
- TurnLoop 改为 Observe/Orient/Act/Reflect/Commit；
- PromptCompiler 不再拼 Wiki 原文。

动作：
1. 新建 ai/kernel/loop.py。
2. RuntimeKernel 改为持有：
   - memory；
   - capability；
   - policy；
   - state；
   - llm；
   - dispatcher。
3. PromptCompiler 改为拼：
   - Identity；
   - Task；
   - MemoryView；
   - CapabilityView；
   - RuntimeState；
   - ResponseContract。
4. ingest_attachments 改为 memory.ingest(files)。
5. state_fragments 中 Wiki 状态改由 MemoryView / MemoryState 提供。

验收：
- Kernel 不 import wiki.hub；
- PromptCompiler 不出现 Agent Wiki、Active Skill Wiki、Wiki Hub 字样；
- 原 Agent loop 功能可运行；
- 工具调用仍正常。

Phase 7：Workbench 重构
------------------------------------------------------------

目标：
- 前端从 Wiki Workbench 升级为 Memory-Native Agent Workbench。

动作：
1. 拆分 app.js：
   - api.js；
   - router.js；
   - pages/intake.js；
   - pages/notes.js；
   - pages/review.js；
   - pages/graph.js；
   - pages/runtime_preview.js；
   - pages/tests.js。
2. build_web.py 支持多 JS/CSS 内联。
3. 新页面：
   - Intake；
   - Notes；
   - Review；
   - Graph；
   - Runtime Preview；
   - Tests。
4. 保留旧搜索和详情页兼容入口。

验收：
- 前端不再以“Wiki 页面治理”为唯一主线；
- Runtime Preview 能展示 MemoryView + CapabilityView + Prompt；
- Graph 页面从 memory_graph_view 取数据；
- Review 页面从 ProposalQueue 取数据。

Phase 8：旧 Wiki 链路降级
------------------------------------------------------------

目标：
- wiki.md 完成迁移；
- WikiHub/WikiWorkbench 不再是核心运行依赖。

动作：
1. 批量将 wiki.md 迁移为 note.md。
2. 将 src/wiki/store 迁移到 data/indexes。
3. 将 src/wiki/workbench/store/drafts 迁移到 data/proposals。
4. ai/src/protocol/compiler.py 降级为兼容编译器或删除。
5. WikiHub 只保留兼容 facade。

验收：
- 新系统无须 WikiHub 也能运行；
- 旧接口仍可读；
- 新接口覆盖全部功能；
- Engine 不依赖 Wiki。

============================================================
15. 当前文件逐项改造建议
============================================================

15.1 __main__.py

当前职责保留：
- 构建前端；
- 启动 uvicorn；
- 检查。

改造：
- banner 改为 Memory-Native Agent Kernel；
- run_checks 新增 check_memory、check_capability、check_kernel；
- build_web 保留，但支持模块化前端构建。

15.2 main_app.py

当前 Starlette 单端口设计保留。

改造：
- /app/wiki/action/{action} 保留兼容；
- 新增 /app/memory/action/{action}；
- 新增 /app/workbench/action/{action}；
- create_app 中路由拆分到 ai/app/api.py。

目标：
main_app.py 只作为启动 glue，不再 import wiki_app.actions。

15.3 ai/wiki_app/actions.py

当前是大 ACTIONS 字典。

改造：
- 短期保留；
- 新增 ai/app/actions.py，按域拆：
  - memory_actions.py；
  - workbench_actions.py；
  - kernel_actions.py；
  - capability_actions.py；
  - legacy_wiki_actions.py。
- 旧 ACTIONS 内部转发新 service。

15.4 ai/wiki_app/service.py

当前过重。

改造：
- 拆成：
  - MemoryAppService；
  - WorkbenchAppService；
  - LegacyWikiCompatService；
  - UserFileEvidenceService。
- 用户文件从 user_files 迁到 EvidenceStore。
- graph/search/schema/draft/publish 分别转给 Memory/Workbench。

15.5 ai/src/runtime/kernel.py

当前直接 import WikiHub。

改造目标：
- 删除 WikiHub import；
- RuntimeKernel.create 中创建 Memory 和 Capability；
- ingest_attachments 改为 memory.ingest；
- state_fragments 改为 memory.state_fragments 或 runtime_state。

15.6 ai/src/runtime/turn.py

当前 loop 很薄，保留思想。

改造：
- begin -> observe；
- 每轮 surface.resolve + prompt.compile 前增加 memory.orient；
- after_tool 后增加 reflect；
- 结束时 memory.capture。

15.7 ai/src/runtime/prompt.py

当前直接拼 Agent Wiki、Active Skill Wiki、Wiki Hub。

改造：
- PromptCompiler.compile(surface) 改为 compile(memory_view, capability_view)；
- 删除 Agent Wiki / Active Skill Wiki / Wiki Hub sections；
- 增加 MemoryView / CapabilityView sections。

15.8 ai/src/runtime/surface.py

当前 ToolSurface 逻辑较好，可迁移。

改造：
- 改名 CapabilitySurfaceResolver；
- 输入 MemoryView.activation_hints；
- 保留权限、类别、activation_mode 逻辑；
- 输出 CapabilityView。

15.9 ai/src/protocol/compiler.py

当前 Wiki Nodes -> ProtocolView。

改造：
- 长期删除 ProtocolCompiler 作为核心链路；
- 短期改为 CapabilityProjector 的兼容适配；
- 从 MemoryNote + Lens 投影 CapabilitySpec；
- ProtocolView 作为 legacy 运行格式保留。

15.10 ai/src/wiki/adapter_bridge.py

当前扫描 src/**/*.md 并以 wiki.md 为特殊命名。

改造：
- 新增 NoteAdapterBridge；
- note.md 优先；
- wiki.md 兼容；
- 路径 kind_hint 改为 NoteStore 逻辑；
- Runtime block 解析降级为 note fields 解析的一部分。

15.11 ai/src/wiki/hub.py

当前是运行时直接使用的 Wiki Hub。

改造：
- 长期降级为 LegacyWikiHub；
- 搜索、read、answer 由 Memory.search / NoteStore.read / Memory.orient 替代；
- ingest_user_files 由 EvidenceStore.ingest 替代；
- system_brief 由 Memory.summary 替代。

15.12 ai/src/wiki/workbench/services/graph_service.py

当前图谱混乱。

改造：
- 不在此处继续增强；
- 新建 ai/memory/graph.py；
- graph_service.py 作为兼容包装；
- wiki_extract_knowledge_graph 转发 memory_graph_view。

15.13 scripts/build_web.py

当前只内联 app.js/style.css。

改造：
- 支持按 manifest 内联多个文件；
- 例如 web/src/manifest.json：
  {
    "css": ["assets/base.css", "assets/graph.css"],
    "js": ["assets/api.js", "assets/router.js", "pages/*.js"]
  }
- 保持 Python build 简单部署优势。

15.14 web/src/assets/app.js

当前单文件过重。

改造：
- 拆分：
  - api.js
  - state.js
  - router.js
  - components/*
  - pages/intake.js
  - pages/notes.js
  - pages/review.js
  - pages/graph.js
  - pages/runtime_preview.js
  - pages/tests.js

============================================================
16. 测试与验收体系
============================================================

16.1 基础检查

python __main__.py --check 应扩展为：

- check_backend
- check_frontend
- check_e2e
- check_memory
- check_note_parser
- check_lens
- check_graph
- check_capability
- check_kernel
- check_runtime_preview

16.2 Memory 测试

必须覆盖：
- note.md 可解析；
- wiki.md 兼容；
- frontmatter 可解析；
- Relations 可生成 declared edges；
- 正文链接可生成 linked edges；
- 缺字段产生 diagnostics；
- runtime_ready 检查有效。

16.3 Graph 测试

必须覆盖：
- 不把实体类型当成普通边；
- 不把作用范围当成普通边；
- declared / linked / inferred / runtime 分类正确；
- candidate 不默认显示；
- graph_neighbors 正确。

16.4 Kernel 测试

必须覆盖：
- Kernel 不 import wiki.hub；
- Prompt 不包含 raw note.md；
- Prompt 包含 MemoryView；
- CapabilityView 中工具权限有效；
- 工具调用结果能进入 Memory.capture。

16.5 Workbench 测试

必须覆盖：
- Intake 生成 Evidence；
- Draft 生成 note；
- Review 接受 Proposal；
- Publish 后 note 状态变化；
- Runtime Preview 输出 MemoryView + CapabilityView。

============================================================
17. 最小可实施路径
============================================================

最小闭环不要一次性大改。建议先做这 10 个文件：

1. ai/memory/types.py
2. ai/memory/note.py
3. ai/memory/store.py
4. ai/memory/lens.py
5. ai/memory/graph.py
6. ai/memory/orient.py
7. ai/capability/types.py
8. ai/capability/surface.py
9. ai/kernel/prompt.py
10. ai/app/actions.py

然后增加 6 个 action：

1. memory_list_notes
2. memory_read_note
3. memory_check_note
4. memory_compile_graph
5. memory_preview_view
6. memory_preview_runtime

这样就可以在不破坏旧系统的前提下，把新架构跑通。

============================================================
18. 关键设计约束
============================================================

必须坚持：

1. Kernel 不直接读 note.md。
2. Capability 不直接读 note.md。
3. Graph 不是真相，只是 Index。
4. Context 不再独立存在，只是 MemoryView。
5. Lens 不做强治理，只做解释提示。
6. LLM 只生成 Proposal，不直接发布。
7. Workbench 是唯一人工确认入口。
8. 所有知识都走统一成熟度模型。
9. note.md 是唯一人机可读知识源格式。
10. Evidence 是原始证据，不直接进入 Runtime。
11. RuntimeReady 是运行门槛，不是发布门槛。
12. 旧 wiki_* action 必须短期兼容，长期降级。

============================================================
19. 最终目标状态
============================================================

最终系统应该变成：

用户请求 + 附件
  -> Kernel.observe
  -> Memory.ingest / orient
  -> MemoryView
  -> Capability.orient
  -> CapabilityView
  -> Kernel.act
  -> Tool / Skill / Workflow
  -> Kernel.reflect
  -> Memory.capture
  -> ProposalQueue
  -> Workbench.review
  -> NoteStore / MemoryGraph / Release

此时：

- Agent 不再被 Wiki 复杂性拖住；
- note.md 可以统一系统知识和业务知识；
- 图谱有来源、有状态、有分类；
- 前端 Workbench 集中处理人参与；
- LLM 能力提升只会增强 Curator，不会破坏 Kernel；
- 原本优雅的 Engine Loop 会保留，并因为 MemoryView/CapabilityView 变得更清晰；
- 知识系统不再是外挂，而成为 Agent 的原生 Memory。

============================================================
20. 总结
============================================================

这次改造不是“把 wiki.md 改成 note.md”这么简单，而是从架构本体上重新定位：

旧架构：
Agent Engine + Wiki + Schema + Graph + Context + Tool

新架构：
Kernel + Memory + Capability + Workbench

旧知识单元：
wiki.md

新知识单元：
note.md = MemoryNote 的人机可读存储格式

旧上下文工程：
从 Wiki、Skill、Tool、Graph 各处拼上下文

新上下文工程：
Memory.orient() 生成 MemoryView

旧工具激活：
Skill 引用 + ToolSurface

新能力激活：
MemoryView.activation_hints + Policy + Capability SurfaceResolver

旧图谱：
Markdown 裸抽 triples

新图谱：
MemoryGraph = note 关系索引，边有 kind/status/evidence

最终，这套系统应成为：

Memory-Native Agent Kernel
即以 Memory 为原生状态、以 note.md 为人机知识载体、以 Lens 为轻解释规则、以 MemoryView 为运行上下文、以 CapabilityView 为能力表面、以 Workbench 为人机治理入口的通用智能体架构。
