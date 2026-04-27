const ACTION_BASE = "/app/wiki/action";
const MEMORY_ACTION_BASE = "/app/memory/action";
const WORKBENCH_ACTION_BASE = "/app/workbench/action";

window.WikiWorkbenchPages = window.WikiWorkbenchPages || {};

const state = {
  query: "",
  mode: "normal",
  filters: { entity_type: "", stage: "", status: "", risk: "", include_disabled: false, only_governance: false, only_draft: false },
  results: [],
  selected: new Set(),
  currentPageId: "",
  currentMarkdown: "",
  currentStatus: null,
  currentHint: null,
  currentDiagnosis: null,
  currentPane: "overview",
  status: null,
  graph: null,
  userPath: "",
  userCurrentFile: "",
  noteQuery: "",
  selectedNoteId: "",
  selectedProposalId: "",
  runtimeTask: "请预览当前任务的 MemoryView、CapabilityView 和 Prompt。",
  testTask: "请检查当前智能体运行预览闭环。",
  message: "",
  error: "",
};

const CN = {
  entity: { "": "全部类型", "页面": "页面", "工具": "工具", "Skill": "Skill", "Agent": "Agent", "Schema": "Schema", "用户文件": "用户文件" },
  stage: { "": "全部阶段", "已发布": "已发布", "草稿": "草稿", "待更新": "待更新", "待诊断": "待诊断", "待发布": "待发布", "已归档": "已归档" },
  status: { "": "全部状态", ok: "正常", update: "需更新", issue: "有问题", risk: "有风险", draft: "有草稿", locked: "已锁定", disabled: "已禁用" },
  risk: { "": "全部风险", none: "无风险", low: "低风险", medium: "中风险", high: "高风险" },
  op: { diagnose: "批量诊断", check_update: "批量检查依赖", draft_update: "批量生成更新草稿" },
};

async function callAction(action, payload = {}) {
  return window.MemoryNativeWorkbench.api.wiki(action, payload);
}

async function callMemoryAction(action, payload = {}) {
  return window.MemoryNativeWorkbench.api.memory(action, payload);
}

async function callWorkbenchAction(action, payload = {}) {
  return window.MemoryNativeWorkbench.api.workbench(action, payload);
}
