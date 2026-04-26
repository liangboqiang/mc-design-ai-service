const ACTION_BASE = "/app/wiki/action";

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

const $ = (id) => document.getElementById(id);
window.addEventListener("error", (event) => showFatal(event.error || event.message));
window.addEventListener("unhandledrejection", (event) => showFatal(event.reason));

function showFatal(error) {
  const root = $("root") || document.body;
  root.innerHTML = `<main class="fatal"><h1>Wiki App 启动失败</h1><pre>${escapeHtml(String(error?.stack || error || "未知错误"))}</pre></main>`;
}

async function callAction(action, payload = {}) {
  const res = await fetch(`${ACTION_BASE}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) {
    const message = data?.error?.message || data?.error || `Action 调用失败：${action}`;
    throw new Error(message);
  }
  return data.data;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function escapeJs(value) { return String(value).replaceAll("\\", "\\\\").replaceAll("'", "\\'"); }
function route(path) { location.hash = path; }
function pageLink(pageId) { return `#/page/${encodeURIComponent(pageId)}`; }
function getHashQuery() { return new URLSearchParams(location.hash.split("?")[1] || ""); }
function setNotice(message = "", error = "") { state.message = message; state.error = error; }
function notice() {
  return `${state.error ? `<div class="notice error">${escapeHtml(state.error)}</div>` : ""}${state.message ? `<div class="notice ok">${escapeHtml(state.message)}</div>` : ""}`;
}
function loadingView(text = "加载中...") { return `<div class="loading">${escapeHtml(text)}</div>`; }
function emptyView(text = "暂无数据") { return `<div class="empty-state">${escapeHtml(text)}</div>`; }
function firstText(obj, keys, fallback = "") {
  for (const key of keys) {
    const value = obj?.[key];
    if (value !== undefined && value !== null && String(value).trim()) return String(value);
  }
  return fallback;
}
function pageIdOf(row) { return firstText(row, ["page_id", "id", "path", "key"], ""); }
function titleOf(row) { return firstText(row, ["title", "name", "label", "page_id", "id"], "未命名页面"); }
function summaryOf(row) { return firstText(row, ["summary", "abstract", "content", "snippet", "description"], "暂无摘要。"); }
function statusOf(row) { return row?.status || { status_labels: [{ type: "ok", label: "正常", pane: "overview" }], risk_level: "none", entity_type: firstText(row, ["entity_type", "type"], "页面") }; }
function entityTypeOf(row) { return statusOf(row).entity_type || firstText(row, ["entity_type", "type", "kind"], "页面"); }

function renderFrame(main, pane = "", options = {}) {
  const root = $("root");
  if (!root) throw new Error("index.html 缺少 #root 节点");
  const command = options.command || "";
  const isHome = (location.hash || "#/") === "#/";
  root.innerHTML = `
    <div class="wiki-shell">
      <aside class="left-nav">
        <div class="brand" onclick="route('#/')">
          <div class="brand-mark">W</div>
          <div><strong>Wiki Workbench</strong><span>V3.3 磁贴门户版</span></div>
        </div>
        <nav class="nav-flat">
          <a href="#/" data-nav="home">首页</a>
          <a href="#/search" data-nav="search">搜索</a>
          <a href="#/graph" data-nav="graph">知识图谱</a>
          <a href="#/backend" data-nav="backend">后台中心</a>
          <a href="#/user" data-nav="user">用户中心</a>
        </nav>
      </aside>
      <main class="main-area">
        <div class="workspace-head ${isHome ? "home-head" : ""}">
          <div class="head-copy"><h1>${escapeHtml(options.title || titleForRoute())}</h1><p>${escapeHtml(options.subtitle || "阅读优先，治理动作按需进入右侧上下文窗格。")}</p></div>
          ${command ? `<div class="head-command">${command}</div>` : ""}
          ${state.status ? `<div class="small-metrics"><span>页</span><strong>${state.status.catalog_count ?? 0}</strong></div>` : ""}
        </div>
        ${notice()}
        <div class="${pane ? "two-column" : "single-column"}">
          <section id="contentColumn" class="content-column">${main}</section>
          ${pane ? `<aside id="contextPane" class="context-pane">${pane}</aside>` : ""}
        </div>
      </main>
    </div>`;
  markActiveNav();
}function titleForRoute() {
  const hash = location.hash || "#/";
  if (hash.startsWith("#/page/")) return "页面详情";
  if (hash.startsWith("#/search")) return "搜索";
  if (hash.startsWith("#/graph")) return "知识图谱";
  if (hash.startsWith("#/backend")) return "后台中心";
  if (hash.startsWith("#/user")) return "用户中心";
  return "首页";
}
function markActiveNav() {
  const hash = location.hash || "#/";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const nav = a.dataset.nav;
    const active = (nav === "home" && hash === "#/") || (nav !== "home" && hash.startsWith(`#/${nav}`));
    a.classList.toggle("active", active);
  });
}

function homeSearchPanel() {
  return `<section class="home-search-panel">
    <div class="home-query-row">
      <input id="homeQueryInput" value="${escapeHtml(state.query)}" placeholder="输入基础检索词..." />
      <button id="homeSearchBtn" class="button primary">组合检索</button>
      <button id="homeClearTagsBtn" class="button ghost">清空</button>
    </div>
    <div class="home-dropdown-row">
      ${renderTermDropdown("对象", "对象类型", ["工具", "Skill", "Agent", "Schema", "用户文件", "页面协议"])}
      ${renderTermDropdown("状态", "治理状态", ["需更新", "有风险", "有问题", "有草稿", "已锁定", "已禁用"])}
      ${renderTermDropdown("流程", "工作流", ["依赖更新", "诊断修复", "Diff", "版本回溯", "图谱关系", "用户建页"])}
      ${renderTermDropdown("业务", "业务域", ["Wiki治理", "工具箱", "页面生成", "知识抽取", "检索增强", "用户文件库"])}
    </div>
    <div class="home-selected-tags" id="homeSelectedTags"></div>
  </section>`;
}
function searchCommand() {
  return `<div class="compact-command search-command">
    <input id="searchQueryInput" value="${escapeHtml(state.query)}" placeholder="搜索页面、工具、Skill、Agent、文件、关系..." />
    <button id="searchRunBtn" class="button primary icon-btn" title="搜索">🔎</button>
    <button id="searchRefreshBtn" class="button ghost icon-btn" title="刷新索引">↻</button>
  </div>`;
}
function pageCommand(pageId = "") {
  return `<div class="compact-command page-command">
    <input id="pageSearchInput" placeholder="在阅读中继续搜索..." />
    <button id="pageSearchBtn" class="button primary icon-btn" title="搜索">🔎</button>
    <button id="pageBackSearchBtn" class="button ghost icon-btn" title="返回搜索" onclick="route('#/search')">↩</button>
  </div>`;
}
function renderTermDropdown(key, title, terms) {
  return `<div class="term-dropdown">
    <button class="term-drop-btn" type="button" data-menu="${escapeHtml(key)}">${escapeHtml(title)} ▾</button>
    <div class="term-menu" data-menu-panel="${escapeHtml(key)}">
      ${terms.map((t) => `<button class="home-term-toggle" type="button" data-term="${escapeHtml(t)}">${escapeHtml(t)}</button>`).join("")}
    </div>
  </div>`;
}
function refreshHomeSelectedTags() {
  const el = $("homeSelectedTags");
  if (!el) return;
  const tags = getSelectedHomeTerms();
  el.innerHTML = tags.length
    ? `组合词条：${tags.map((t) => `<span class="selected-tag">${escapeHtml(t)}</span>`).join("")}`
    : `选择下拉词条用于加工 query，不会单独触发搜索。`;
}
function getSelectedHomeTerms() {
  return [...document.querySelectorAll(".home-term-toggle.active")].map((x) => x.dataset.term).filter(Boolean);
}
function buildHomeQuery() {
  const base = ($("homeQueryInput")?.value || "").trim();
  const terms = getSelectedHomeTerms();
  return [base, ...terms].filter(Boolean).join(" ");
}
function bindHomeSearchPanel() {
  $("homeSearchBtn").onclick = () => {
    state.query = buildHomeQuery();
    route(`#/search?q=${encodeURIComponent(state.query)}`);
    renderSearch(true);
  };
  $("homeQueryInput").onkeydown = (e) => { if (e.key === "Enter") $("homeSearchBtn").click(); };
  $("homeClearTagsBtn").onclick = () => {
    document.querySelectorAll(".home-term-toggle").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".term-menu").forEach((x) => x.classList.remove("open"));
    refreshHomeSelectedTags();
  };
  document.querySelectorAll(".term-drop-btn").forEach((btn) => {
    btn.onclick = () => {
      const key = btn.dataset.menu;
      document.querySelectorAll(".term-menu").forEach((panel) => {
        panel.classList.toggle("open", panel.dataset.menuPanel === key && !panel.classList.contains("open"));
      });
    };
  });
  document.querySelectorAll(".home-term-toggle").forEach((btn) => {
    btn.onclick = () => {
      btn.classList.toggle("active");
      refreshHomeSelectedTags();
    };
  });
  refreshHomeSelectedTags();
}
function bindSearchCommand() {
  $("searchRunBtn").onclick = () => {
    state.query = $("searchQueryInput").value.trim();
    route(`#/search?q=${encodeURIComponent(state.query)}`);
    renderSearch(true);
  };
  $("searchQueryInput").onkeydown = (e) => { if (e.key === "Enter") $("searchRunBtn").click(); };
  $("searchRefreshBtn").onclick = refreshIndex;
}
function bindPageCommand() {
  $("pageSearchBtn").onclick = () => {
    state.query = $("pageSearchInput").value.trim();
    route(`#/search?q=${encodeURIComponent(state.query)}`);
    renderSearch(true);
  };
  $("pageSearchInput").onkeydown = (e) => { if (e.key === "Enter") $("pageSearchBtn").click(); };
}

async function refreshIndex() {
  setNotice("正在刷新索引...");
  updateNotice();
  try {
    await callAction("wiki_refresh_index", { extract_graph: true });
    state.status = await callAction("wiki_server_status", {});
    setNotice("索引刷新完成。");
  } catch (error) {
    setNotice("", String(error.message || error));
  }
  updateNotice();
}
function updateNotice() {
  const existing = document.querySelector(".notice");
  if (existing) existing.outerHTML = notice() || "";
}

function statusChips(status, options = {}) {
  const labels = status?.status_labels || [{ type: "ok", label: "正常", pane: "overview" }];
  return `<div class="status-chips">${labels.map((item) => {
    const label = item.label || CN.status[item.type] || "状态";
    return `<button class="status-chip ${escapeHtml(item.type || "ok")}" data-pane="${escapeHtml(item.pane || "overview")}" data-page="${escapeHtml(options.pageId || "")}" data-kind="${escapeHtml(options.kind || "")}">${escapeHtml(label)}</button>`;
  }).join("")}</div>`;
}
function compactStatus(status) {
  return statusChips(status).replaceAll("<button", "<span").replaceAll("</button>", "</span>");
}
function metric(label, value) { return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`; }

async function renderHome() {
  renderFrame(loadingView("正在加载首页..."), "", { title: "首页", subtitle: "磁贴门户：状态、链接、缩略图和核心动作。" });
  try {
    state.status = await callAction("wiki_server_status", {});
    const overview = await callAction("wiki_backend_overview", { query: "", limit: 8, include_disabled: false }).catch(() => ({ rows: [], stats: {} }));
    const graph = await callAction("wiki_extract_knowledge_graph", { include_graph: true, write_store: false, include_disabled: false }).catch(() => ({ nodes: [], edges: [], fallback: true }));
    const rows = overview.rows || [];
    const stats = overview.stats || {};
    const recent = rows.slice(0, 4);
    const main = `
      <section class="home-hero-card">
        <div class="hero-copy">
          <h2>工程 Wiki 总览</h2>
          <p>用磁贴查看关键状态、进入核心模块，并通过组合词条加工更准确的检索。</p>
        </div>
        ${homeSearchPanel()}
      </section>
      <section class="home-tile-grid">
        ${renderHistoryTile(recent)}
        ${renderGraphTile(graph)}
        ${renderBackendTile(stats)}
        ${renderUserTile()}
      </section>`;
    renderFrame(main, "", { title: "首页", subtitle: "历史详情、知识图谱、后台看板、用户入口。", command: "" });
    bindHomeSearchPanel();
    drawHomeGraphMini(graph);
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("首页加载失败。")}`, "", { title: "首页" });
  }
}
function renderHistoryTile(rows) {
  return `<article class="portal-tile history-tile">
    <div class="tile-head"><span class="tile-icon">🕘</span><div><h3>历史详情页</h3><small>最近可进入页面</small></div></div>
    <div class="tile-list">
      ${rows.length ? rows.map((r) => `<a href="${pageLink(pageIdOf(r))}">${escapeHtml(titleOf(r)).slice(0, 20)}<span>›</span></a>`).join("") : `<a href="#/search">进入搜索<span>›</span></a>`}
    </div>
  </article>`;
}
function renderGraphTile(graph) {
  const n = (graph.nodes || graph.graph?.nodes || []).length || 0;
  const e = (graph.edges || graph.graph?.edges || []).length || 0;
  return `<article class="portal-tile graph-tile">
    <div class="tile-head"><span class="tile-icon">◎</span><div><h3>知识图谱</h3><small>${n} 节点 · ${e} 关系</small></div><a class="tile-link" href="#/graph">↗</a></div>
    <div id="homeGraphMini" class="home-graph-mini"></div>
  </article>`;
}
function renderBackendTile(stats) {
  return `<article class="portal-tile backend-tile">
    <div class="tile-head"><span class="tile-icon">▦</span><div><h3>后台中心</h3><small>全仓看板</small></div><a class="tile-link" href="#/backend">↗</a></div>
    <div class="dashboard-mini">
      ${metric("页", stats.total ?? state.status?.catalog_count ?? 0)}
      ${metric("更", stats.update_required ?? 0)}
      ${metric("题", stats.issue ?? 0)}
      ${metric("稿", stats.draft ?? 0)}
    </div>
    <div class="tile-actions">
      <button class="button ghost small" onclick="refreshIndex()">↻ 全量刷新</button>
      <button class="button ghost small" onclick="route('#/backend')">▦ 看板</button>
    </div>
  </article>`;
}
function renderUserTile() {
  return `<article class="portal-tile user-tile">
    <div class="tile-head"><span class="tile-icon">◌</span><div><h3>用户中心</h3><small>文件与治理对话</small></div><a class="tile-link" href="#/user">↗</a></div>
    <div class="user-chat-mini">
      <div class="chat-bubble">我上传了文件，应该生成哪些 wiki.md？</div>
      <div class="chat-input-mini">输入治理请求… <span>↗</span></div>
    </div>
  </article>`;
}
function drawHomeGraphMini(data) {
  const el = $("homeGraphMini");
  if (!el) return;
  const graph = normalizeGraphData(data || {});
  const nodes = graph.nodes.slice(0, 9);
  const edges = graph.edges.slice(0, 12);
  const ids = new Set(nodes.map((n) => n.id));
  const pos = nodes.map((n, i) => {
    const a = Math.PI * 2 * i / Math.max(1, nodes.length);
    return { id: n.id, label: n.label, x: 70 + Math.cos(a) * 48, y: 55 + Math.sin(a) * 34 };
  });
  const pmap = new Map(pos.map((p) => [p.id, p]));
  el.innerHTML = `<svg viewBox="0 0 140 110" class="mini-svg">
    ${edges.filter((e) => ids.has(e.source) && ids.has(e.target)).map((e) => { const s=pmap.get(e.source), t=pmap.get(e.target); return s&&t ? `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}"></line>` : ""; }).join("")}
    ${pos.map((p, i) => `<circle cx="${p.x}" cy="${p.y}" r="${i===0?7:5}"></circle>`).join("")}
  </svg>`;
}

function renderSearchCard(row) {
  const pageId = pageIdOf(row);
  const status = statusOf(row);
  const checked = state.selected.has(pageId) ? "checked" : "";
  return `<article class="search-card" data-page="${escapeHtml(pageId)}">
    <input class="select-result" type="checkbox" data-page="${escapeHtml(pageId)}" ${checked}/>
    <div class="search-card-main">
      <div class="search-title-line"><a href="${pageLink(pageId)}" class="result-title">${escapeHtml(titleOf(row))}</a><span class="entity-pill">${escapeHtml(entityTypeOf(row))}</span></div>
      <p>${escapeHtml(summaryOf(row)).slice(0, 220)}</p>
      <code>${escapeHtml(pageId)}</code>
      <div class="matched-reason">命中：${escapeHtml(firstText(row, ["matched_reason", "reason"], "标题 / 摘要 / 元词条 / 关系"))}</div>
      ${statusChips(status, { pageId, kind: "search" })}
    </div>
  </article>`;
}

function optionList(map, current) {
  return Object.entries(map).map(([value, label]) => `<option value="${escapeHtml(value)}" ${value === current ? "selected" : ""}>${escapeHtml(label)}</option>`).join("");
}
function renderSearchControls() {
  return `<section class="search-controls">
    <div class="mode-row">
      <label><input type="radio" name="searchMode" value="normal" ${state.mode === "normal" ? "checked" : ""}/> 常规检索</label>
      <label><input type="radio" name="searchMode" value="graph" ${state.mode === "graph" ? "checked" : ""}/> 图谱增强</label>
      <label><input type="radio" name="searchMode" value="qa" ${state.mode === "qa" ? "checked" : ""}/> 语义问答</label>
    </div>
    <div class="advanced-row">
      <label class="select-label"><span>类型</span><select id="entityFilter">${optionList(CN.entity, state.filters.entity_type)}</select></label>
      <label class="select-label"><span>阶段</span><select id="stageFilter">${optionList(CN.stage, state.filters.stage)}</select></label>
      <label class="select-label"><span>状态</span><select id="statusFilter">${optionList(CN.status, state.filters.status)}</select></label>
      <label class="select-label"><span>风险</span><select id="riskFilter">${optionList(CN.risk, state.filters.risk)}</select></label>
      <button id="applyFiltersBtn" class="button primary">应用筛选</button>
    </div>
    <div class="toggle-row">
      <label><input type="checkbox" id="includeDisabled" ${state.filters.include_disabled ? "checked" : ""}/> 显示禁用页面</label>
      <label><input type="checkbox" id="onlyGovernance" ${state.filters.only_governance ? "checked" : ""}/> 仅待治理</label>
      <label><input type="checkbox" id="onlyDraft" ${state.filters.only_draft ? "checked" : ""}/> 仅有草稿</label>
    </div>
  </section>`;
}
async function renderSearch(forceFetch = false) {
  const params = getHashQuery();
  if (params.has("q")) state.query = params.get("q") || "";
  renderFrame(loadingView("正在检索..."), renderSearchPane(), { title: "搜索", subtitle: "筛选项调整不会立即刷新，点击“应用筛选”后再检索。", command: searchCommand() });
  bindSearchCommand();
  try {
    const payload = {
      query: state.query,
      limit: 60,
      include_disabled: state.filters.include_disabled,
      entity_type: state.filters.entity_type,
      stage: state.filters.stage,
      status: state.filters.status,
      risk: state.filters.risk,
    };
    const data = await callAction(state.mode === "graph" ? "wiki_graph_enhanced_search" : "wiki_search_with_status", payload);
    let rows = state.mode === "graph" ? (data.results || []) : (data.results || []);
    rows = rows.map((row) => ({ ...row, status: row.status || statusOf(row) }));
    if (state.filters.only_governance) rows = rows.filter((r) => {
      const s = statusOf(r);
      return s.update_required || s.issue_count || s.draft_count || s.risk_level !== "none";
    });
    if (state.filters.only_draft) rows = rows.filter((r) => statusOf(r).draft_count);
    state.results = rows;
    state.selected = new Set([...state.selected].filter((id) => rows.some((r) => pageIdOf(r) === id)));
    renderSearchLoaded(data.stats || computeStats(rows));
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("搜索失败。")}`, renderSearchPane(), { title: "搜索", command: searchCommand() });
    bindSearchCommand();
  }
}
function computeStats(rows) {
  return { total: rows.length, update_required: rows.filter((r) => statusOf(r).update_required).length, issue: rows.filter((r) => statusOf(r).issue_count).length, draft: rows.filter((r) => statusOf(r).draft_count).length };
}
function renderSearchLoaded(stats) {
  const main = `${renderSearchControls()}
    <section class="result-toolbar"><label><input id="selectAllResults" type="checkbox" /> 全选当前结果</label><span>已选 <strong id="selectedCount">${state.selected.size}</strong> 项</span></section>
    <section class="result-summary">${metric("结果", stats.total ?? state.results.length)}${metric("需更新", stats.update_required ?? 0)}${metric("问题", stats.issue ?? 0)}${metric("草稿", stats.draft ?? 0)}</section>
    <section id="resultsList" class="results-list">${state.results.map(renderSearchCard).join("") || emptyView("没有结果。")}</section>`;
  renderFrame(main, renderSearchPane(), { title: "搜索", subtitle: `${state.results.length} 条结果；复选框选择只更新右侧窗格，不会重新检索。`, command: searchCommand() });
  bindSearchCommand();
  wireSearchControls();
  wireResultCards(true);
}
function wireSearchControls() {
  document.querySelectorAll("[name=searchMode]").forEach((el) => el.onchange = () => { state.mode = el.value; });
  $("entityFilter").onchange = (e) => { state.filters.entity_type = e.target.value; };
  $("stageFilter").onchange = (e) => { state.filters.stage = e.target.value; };
  $("statusFilter").onchange = (e) => { state.filters.status = e.target.value; };
  $("riskFilter").onchange = (e) => { state.filters.risk = e.target.value; };
  $("includeDisabled").onchange = (e) => { state.filters.include_disabled = e.target.checked; };
  $("onlyGovernance").onchange = (e) => { state.filters.only_governance = e.target.checked; };
  $("onlyDraft").onchange = (e) => { state.filters.only_draft = e.target.checked; };
  $("applyFiltersBtn").onclick = () => renderSearch(true);
  $("selectAllResults").onchange = (e) => {
    state.results.forEach((r) => { const id = pageIdOf(r); if (id) e.target.checked ? state.selected.add(id) : state.selected.delete(id); });
    syncSelectionUi();
  };
}
function wireResultCards(canSelect = true) {
  document.querySelectorAll(".select-result").forEach((el) => {
    el.onchange = () => {
      const id = el.dataset.page;
      if (el.checked) state.selected.add(id); else state.selected.delete(id);
      syncSelectionUi();
    };
  });
  document.querySelectorAll('.status-chip[data-kind="search"]').forEach((chip) => chip.onclick = (event) => {
    event.preventDefault();
    state.selected.clear();
    updateContextPane(renderResultContextPane(chip.dataset.page, chip.dataset.pane));
  });
}
function syncSelectionUi() {
  document.querySelectorAll(".select-result").forEach((el) => { el.checked = state.selected.has(el.dataset.page); });
  if ($("selectedCount")) $("selectedCount").textContent = String(state.selected.size);
  updateContextPane(renderSearchPane());
}
function updateContextPane(html) { if ($("contextPane")) $("contextPane").innerHTML = html; }
function renderSearchPane() {
  if (state.selected.size) return renderBatchPane();
  return `<div class="pane-card"><h3>搜索上下文</h3><p>勾选结果后右侧显示批量治理流程；点击状态标签查看单条治理建议。</p><div class="pane-action-grid"><button class="button ghost" onclick="selectAllVisible()">全选当前结果</button><button class="button ghost" onclick="state.filters.only_governance=true; renderSearch(true)">仅看待治理</button><button class="button ghost" onclick="route('#/backend')">后台中心</button></div></div>`;
}
function selectAllVisible() {
  state.results.forEach((r) => { const id = pageIdOf(r); if (id) state.selected.add(id); });
  syncSelectionUi();
}
function renderResultContextPane(pageId, pane) {
  const row = state.results.find((r) => pageIdOf(r) === pageId) || {};
  const status = statusOf(row);
  return `<div class="pane-card"><h3>${escapeHtml(titleOf(row))}</h3>${compactStatus(status)}<p>${escapeHtml(summaryOf(row))}</p><code>${escapeHtml(pageId)}</code><div class="pane-action-grid"><button class="button primary" onclick="route('${pageLink(pageId)}')">打开页面</button><button class="button ghost" onclick="runPaneAction('wiki_page_status_summary',{page_id:'${escapeJs(pageId)}'})">状态评估</button><button class="button ghost" onclick="runPaneAction('wiki_page_update_hint',{page_id:'${escapeJs(pageId)}'})">检查依赖</button><button class="button ghost" onclick="runPaneAction('wiki_diagnose_page',{page_id:'${escapeJs(pageId)}'})">诊断页面</button></div><pre id="paneOutput"></pre></div>`;
}
function renderBatchPane() {
  const ids = [...state.selected];
  return `<div class="pane-card batch-pane"><h3>批量治理流程</h3><p>已选 ${ids.length} 个页面。可全选、取消、自定义选择后再选择治理方式。</p>
    <label class="select-label"><span>治理方式</span><select id="batchOperation">${optionList(CN.op, "diagnose")}</select></label>
    <div class="selected-pages">${ids.map((id) => `<label><input type="checkbox" class="selected-page-check" data-page="${escapeHtml(id)}" checked /> ${escapeHtml(id)}</label>`).join("")}</div>
    <div class="pane-action-grid"><button class="button primary" onclick="runBatchGovernance()">执行治理</button><button class="button ghost" onclick="clearSelected()">清空选择</button></div>
    <pre id="batchOutput"></pre></div>`;
}
function clearSelected() { state.selected.clear(); syncSelectionUi(); }
async function runBatchGovernance() {
  const ids = [...document.querySelectorAll(".selected-page-check")].filter((x) => x.checked).map((x) => x.dataset.page);
  try { $("batchOutput").textContent = JSON.stringify(await callAction("wiki_batch_governance", { page_ids: ids, operation: $("batchOperation").value, author: "wiki_app" }), null, 2); }
  catch (e) { $("batchOutput").textContent = String(e.message || e); }
}
async function runPaneAction(action, payload) {
  try { $("paneOutput").textContent = JSON.stringify(await callAction(action, payload), null, 2); }
  catch (e) { $("paneOutput").textContent = String(e.message || e); }
}

function markdownToHtml(md) {
  let html = escapeHtml(md || "");
  html = html.replace(/^### (.*)$/gm, "<h3>$1</h3>").replace(/^## (.*)$/gm, "<h2>$1</h2>").replace(/^# (.*)$/gm, "<h1>$1</h1>");
  html = html.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, (m, id, label) => `<a href="${pageLink(id.trim())}" class="wiki-link">${escapeHtml(label.trim())}</a>`);
  html = html.replace(/\[\[([^\]]+)\]\]/g, (m, id) => `<a href="${pageLink(id.trim())}" class="wiki-link">${escapeHtml(id.trim())}</a>`);
  html = html.replace(/^- (.*)$/gm, "<li>$1</li>").replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>").replace(/\n{2,}/g, "</p><p>");
  return `<article class="wiki-article"><p>${html}</p></article>`;
}
function tocFromMarkdown(md) {
  const headers = [];
  String(md || "").split(/\r?\n/).forEach((line) => { const m = line.match(/^(#{1,3})\s+(.+)$/); if (m) headers.push({ level: m[1].length, title: m[2].trim() }); });
  return headers.length ? `<ol class="toc-list">${headers.map((h) => `<li class="l${h.level}">${escapeHtml(h.title)}</li>`).join("")}</ol>` : `<div class="toc-empty">暂无目录</div>`;
}
function extractInfo(markdown, pageId) {
  const info = { page_id: pageId };
  for (const line of String(markdown || "").split(/\r?\n/)) {
    const m = line.match(/^\s*-\s*([^：:]+)[：:]\s*(.*)$/);
    if (m) info[m[1].trim()] = m[2].trim();
  }
  return info;
}
function titleFromMarkdown(md) { const m = String(md || "").match(/^#\s+(.+)$/m); return m ? m[1].trim() : ""; }
function summaryFromMarkdown(md) { return String(md || "").replace(/^#+\s+.*$/gm, "").replace(/[-*]\s*[^：:]+[：:].*$/gm, "").trim().split(/\n{2,}/)[0]?.slice(0, 180) || "暂无摘要。"; }

async function renderPage(pageId, pane = state.currentPane || "overview") {
  state.currentPageId = pageId;
  state.currentPane = pane;
  renderFrame(loadingView("正在读取页面..."), loadingView("准备上下文窗格..."), { title: "页面详情", subtitle: pageId, command: pageCommand(pageId) });
  bindPageCommand();
  try {
    const [source, status, hint, diagnosis] = await Promise.all([
      callAction("wiki_read_source", { page_id: pageId }),
      callAction("wiki_page_status_summary", { page_id: pageId }),
      callAction("wiki_page_update_hint", { page_id: pageId }).catch((e) => ({ requires_update: true, message: String(e.message || e), changed_files: [] })),
      callAction("wiki_diagnose_page", { page_id: pageId }).catch(() => ({ issues: [] })),
    ]);
    state.currentMarkdown = source.markdown || "";
    state.currentStatus = status;
    state.currentHint = hint;
    state.currentDiagnosis = diagnosis;
    const info = extractInfo(state.currentMarkdown, pageId);
    const main = `<section class="page-header-compact"><div><h2>${escapeHtml(info["实体名称"] || titleFromMarkdown(state.currentMarkdown) || pageId)}</h2><p>${escapeHtml(info["摘要"] || summaryFromMarkdown(state.currentMarkdown))}</p><code>${escapeHtml(pageId)}</code></div>${statusChips(status, { pageId, kind: "page" })}</section>
      <div class="reader-grid"><aside class="toc">${tocFromMarkdown(state.currentMarkdown)}</aside><article class="article-surface"><div class="article-tabs"><button id="readTab" class="tab active">阅读</button><button id="sourceTab" class="tab">源码</button></div><div id="articleBody">${markdownToHtml(state.currentMarkdown)}</div></article></div>`;
    renderFrame(main, renderPagePane(pane, { pageId, info, status, hint, diagnosis }), { title: "页面详情", subtitle: "详情页使用紧凑页内命令区，阅读内容优先。", command: pageCommand(pageId) });
    bindPageCommand();
    $("readTab").onclick = () => { $("readTab").classList.add("active"); $("sourceTab").classList.remove("active"); $("articleBody").innerHTML = markdownToHtml(state.currentMarkdown); };
    $("sourceTab").onclick = () => { $("sourceTab").classList.add("active"); $("readTab").classList.remove("active"); $("articleBody").innerHTML = `<textarea id="sourceEditor" class="source-editor">${escapeHtml(state.currentMarkdown)}</textarea>`; };
    document.querySelectorAll('.status-chip[data-kind="page"]').forEach((chip) => chip.onclick = () => renderPage(pageId, chip.dataset.pane || "overview"));
    wirePagePaneButtons(pageId);
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("页面读取失败。")}`, "", { title: "页面详情", command: pageCommand(pageId) });
    bindPageCommand();
  }
}
function renderPagePane(pane, data) {
  const { pageId, info, status, hint, diagnosis } = data;
  const tabs = ["overview", "update", "diagnose", "diff", "version", "risk", "graph", "draft"].map((p) => `<button class="pane-tab ${pane === p ? "active" : ""}" onclick="renderPage('${escapeJs(pageId)}','${p}')">${({ overview: "信息", update: "更新", diagnose: "诊断", diff: "Diff", version: "版本", risk: "风险", graph: "关系", draft: "草稿" })[p]}</button>`).join("");
  let body = "";
  if (pane === "update") body = `<div class="pane-card"><h3>依赖更新</h3><p>${escapeHtml(hint?.message || "检查真实文件变化。")}</p><div class="mini-list">${(hint?.changed_files || []).slice(0, 8).map((f) => `<div class="mini-item"><strong>${escapeHtml(f.path || f.file || "依赖文件")}</strong><span>${escapeHtml(f.status || f.change || "changed")}</span></div>`).join("") || "<div class='empty-state compact'>暂无变化详情</div>"}</div><button class="button primary full" id="fileStatusBtn">依赖详情</button><button class="button ghost full" id="diffUpdateBtn">差异化更新草稿</button><button class="button ghost full" id="fullUpdateBtn">全量更新草稿</button><pre id="pagePaneOutput"></pre></div>`;
  else if (pane === "diagnose") body = `<div class="pane-card"><h3>诊断修复</h3><div class="mini-list">${(diagnosis?.issues || []).slice(0, 8).map((issue, i) => `<div class="mini-item"><strong>${escapeHtml(issue.message || issue.title || issue.id || "问题")}</strong><button class="button ghost small diagnose-fix" data-action="${escapeHtml(issue.id || `fix_${i}`)}">生成修复草稿</button></div>`).join("") || "<div class='empty-state compact'>暂无诊断问题</div>"}</div><button class="button primary full" id="diagnoseBtn">重新诊断</button><pre id="pagePaneOutput"></pre></div>`;
  else if (pane === "diff") body = `<div class="pane-card"><h3>Diff 查看</h3><input id="draftIdInput" placeholder="draft_id" /><button class="button primary full" id="diffDraftBtn">查看草稿 Diff</button><pre id="pagePaneOutput"></pre></div>`;
  else if (pane === "version") body = `<div class="pane-card"><h3>版本查询与回溯</h3><button class="button primary full" id="historyBtn">读取版本历史</button><input id="rollbackCommit" placeholder="commit hash" /><button class="button ghost full" id="rollbackBtn">创建回滚草稿</button><pre id="pagePaneOutput"></pre></div>`;
  else if (pane === "risk") body = `<div class="pane-card"><h3>风险评估</h3>${infoRow("风险等级", CN.risk[status.risk_level] || status.risk_level)}${infoRow("问题数量", status.issue_count || 0)}${infoRow("变化文件", status.changed_file_count || 0)}${infoRow("草稿数量", status.draft_count || 0)}<button class="button primary full" id="riskRefreshBtn">重新评估</button><pre id="pagePaneOutput"></pre></div>`;
  else if (pane === "graph") body = `<div class="pane-card"><h3>局部关系</h3><div id="localGraph" class="local-graph">${loadingView("读取局部图谱...")}</div><button class="button ghost full" onclick="route('#/graph?q=${encodeURIComponent(pageId)}')">打开全局图谱</button></div>`;
  else if (pane === "draft") body = `<div class="pane-card"><h3>草稿处理</h3><p>编辑、诊断、更新都会先生成草稿。</p><button class="button primary full" id="saveDraftBtn">保存当前源码为草稿</button><pre id="pagePaneOutput"></pre></div>`;
  else body = `<div class="pane-card"><h3>信息框</h3>${infoRow("实体类型", info["实体类型"] || status.entity_type || "页面")}${infoRow("页面 ID", pageId)}${infoRow("阶段", status.stage || "已发布")}${infoRow("锁定", status.locked ? "已锁定" : "未锁定")}${infoRow("禁用", status.disabled ? "已禁用" : "未禁用")}${infoRow("作用范围", info["作用范围"] || "未声明")}${compactStatus(status)}<button class="button ghost full" onclick="renderPage('${escapeJs(pageId)}','graph')">查看局部关系</button></div>`;
  return `<div class="pane-tabs">${tabs}</div>${body}`;
}
function infoIcon(k) {
  return ({ "实体类型": "⌁", "页面 ID": "#", "阶段": "◷", "锁定": "🔒", "禁用": "⊘", "作用范围": "⌖", "风险等级": "⚠", "问题数量": "!", "变化文件": "↻", "草稿数量": "✎" })[k] || "•";
}
function infoRow(k, v) { return `<div class="info-row" title="${escapeHtml(k)}"><span class="info-icon">${infoIcon(k)}</span><strong>${escapeHtml(v)}</strong></div>`; }
function wirePagePaneButtons(pageId) {
  if ($("fileStatusBtn")) $("fileStatusBtn").onclick = () => pagePaneAction("wiki_page_file_status", { page_id: pageId });
  if ($("diffUpdateBtn")) $("diffUpdateBtn").onclick = () => pagePaneAction("wiki_update_page_diff", { page_id: pageId, author: "wiki_app" });
  if ($("fullUpdateBtn")) $("fullUpdateBtn").onclick = () => pagePaneAction("wiki_update_page_full", { page_id: pageId, author: "wiki_app" });
  if ($("diagnoseBtn")) $("diagnoseBtn").onclick = () => pagePaneAction("wiki_diagnose_page", { page_id: pageId });
  document.querySelectorAll(".diagnose-fix").forEach((btn) => btn.onclick = () => pagePaneAction("wiki_apply_diagnosis_fix", { page_id: pageId, action_id: btn.dataset.action, author: "wiki_app" }));
  if ($("diffDraftBtn")) $("diffDraftBtn").onclick = () => pagePaneAction("wiki_diff_draft", { draft_id: $("draftIdInput").value });
  if ($("historyBtn")) $("historyBtn").onclick = () => pagePaneAction("wiki_page_history", { page_id: pageId, limit: 20 });
  if ($("rollbackBtn")) $("rollbackBtn").onclick = () => pagePaneAction("wiki_create_rollback_draft", { page_id: pageId, commit: $("rollbackCommit").value, author: "wiki_app" });
  if ($("riskRefreshBtn")) $("riskRefreshBtn").onclick = () => pagePaneAction("wiki_page_status_summary", { page_id: pageId });
  if ($("saveDraftBtn")) $("saveDraftBtn").onclick = async () => {
    const editor = $("sourceEditor");
    await pagePaneAction("wiki_save_draft", { page_id: pageId, markdown: editor ? editor.value : state.currentMarkdown, author: "wiki_app", reason: "页面详情保存" });
  };
  if ($("localGraph")) drawLocalGraph(pageId);
}
async function pagePaneAction(action, payload) {
  try { $("pagePaneOutput").textContent = JSON.stringify(await callAction(action, payload), null, 2); }
  catch (e) { $("pagePaneOutput").textContent = String(e.message || e); }
}

const GraphAdapter = {
  render(container, graph, options = {}) {
    if (window.cytoscape) return this.renderCytoscape(container, graph, options);
    return this.renderSvg(container, graph, options);
  },
  renderCytoscape(container, graph, options = {}) {
    container.innerHTML = "";
    const elements = [...graph.nodes.map((n) => ({ data: { id: n.id, label: n.label, type: n.type, page_id: n.page_id } })), ...graph.edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.label } }))];
    const cy = window.cytoscape({ container, elements, layout: { name: "cose", animate: false } });
    cy.on("tap", "node", (evt) => options.onNodeClick?.(evt.target.data()));
    return cy;
  },
  renderSvg(container, graph, options = {}) {
    const width = Math.max(720, container.clientWidth || 720), height = Math.max(460, container.clientHeight || 460);
    const nodes = (graph.nodes || []).slice(0, 140), ids = new Set(nodes.map((n) => n.id));
    const edges = (graph.edges || []).filter((e) => ids.has(e.source) && ids.has(e.target)).slice(0, 240);
    const cx = width / 2, cy = height / 2, r = Math.min(width, height) * 0.38, pos = new Map();
    nodes.forEach((n, i) => { const a = Math.PI * 2 * i / Math.max(1, nodes.length); pos.set(n.id, { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r }); });
    const color = (type) => ({ tool: "#7c3aed", skill: "#16a34a", agent: "#ea580c", schema: "#64748b", page: "#2563eb", entity: "#0891b2" }[String(type).toLowerCase()] || "#2563eb");
    container.innerHTML = `<svg class="graph-svg" viewBox="0 0 ${width} ${height}"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"></path></marker></defs><g>${edges.map((e) => { const s = pos.get(e.source), t = pos.get(e.target); return s && t ? `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" marker-end="url(#arrow)"></line>` : ""; }).join("")}</g><g>${nodes.map((n) => { const p = pos.get(n.id); return `<g class="graph-node" data-id="${escapeHtml(n.id)}" transform="translate(${p.x},${p.y})"><circle r="15" fill="${color(n.type)}"></circle><text y="32">${escapeHtml(n.label).slice(0, 16)}</text></g>`; }).join("")}</g></svg>`;
    container.querySelectorAll("[data-id]").forEach((el) => {
      el.onclick = () => options.onNodeClick?.(nodes.find((n) => n.id === el.dataset.id));
      el.ondblclick = () => { const n = nodes.find((x) => x.id === el.dataset.id); if (n) route(pageLink(n.page_id || n.id)); };
    });
  }
};
function normalizeGraphData(data) {
  const graph = data?.graph || data || {};
  let nodes = graph.nodes || data.nodes || [], edges = graph.edges || graph.links || data.edges || [], triples = graph.triples || data.triples || [];
  if ((!nodes.length || !edges.length) && Array.isArray(triples)) {
    const map = new Map();
    edges = triples.slice(0, 300).map((t, i) => {
      const source = String(Array.isArray(t) ? t[0] : t.source || ""), label = String(Array.isArray(t) ? t[1] : t.label || t.relation || ""), target = String(Array.isArray(t) ? t[2] : t.target || "");
      if (source) map.set(source, { id: source, label: source, type: "entity" });
      if (target) map.set(target, { id: target, label: target, type: "entity" });
      return { id: `edge-${i}`, source, target, label };
    }).filter((e) => e.source && e.target);
    nodes = [...map.values()];
  }
  nodes = nodes.map((n) => ({ id: String(n.id || n.page_id || n.label || n.name), label: String(n.label || n.title || n.name || n.id || n.page_id), type: String(n.type || n.entity_type || "page"), page_id: String(n.page_id || n.id || ""), summary: String(n.summary || n.description || "") })).filter((n) => n.id);
  edges = edges.map((e, i) => ({ id: String(e.id || `edge-${i}`), source: String(e.source || e.from || ""), target: String(e.target || e.to || ""), label: String(e.label || e.relation || e.type || "") })).filter((e) => e.source && e.target);
  return { nodes, edges, triples, fallback: data?.fallback || graph?.fallback };
}
async function drawLocalGraph(pageId) {
  try { GraphAdapter.render($("localGraph"), normalizeGraphData(await callAction("wiki_graph_neighbors", { page_id: pageId, depth: 1, include_disabled: false })), { onNodeClick: (node) => { if (node?.page_id || node?.id) route(pageLink(node.page_id || node.id)); } }); }
  catch { $("localGraph").innerHTML = `<div class="empty-state compact">局部图谱暂无数据</div>`; }
}
async function renderGraph() {
  renderFrame(loadingView("正在读取图谱..."), "", { title: "知识图谱" });
  try {
    const graph = normalizeGraphData(await callAction("wiki_extract_knowledge_graph", { include_graph: true, write_store: true, include_disabled: state.filters.include_disabled }));
    const main = `<section class="graph-toolbar"><input id="graphQuery" placeholder="过滤节点或关系..." /><select id="graphType"><option value="">全部类型</option><option value="tool">工具</option><option value="skill">Skill</option><option value="agent">Agent</option><option value="page">页面</option></select><button id="graphFilterBtn" class="button primary">筛选</button></section><div class="graph-page"><section id="graphCanvas" class="graph-canvas"></section><aside id="graphDetail" class="context-pane embedded"><h3>节点摘要</h3><p>${graph.fallback ? "当前为降级图谱，后端抽取失败但页面不中断。" : "点击节点查看摘要，双击节点打开页面。"}</p></aside></div><section class="panel"><h3>三元组样例</h3><pre>${escapeHtml(JSON.stringify((graph.triples || []).slice(0, 30), null, 2))}</pre></section>`;
    renderFrame(main, "", { title: "知识图谱", subtitle: `节点 ${graph.nodes.length} 个，关系 ${graph.edges.length} 条` });
    const draw = (g) => GraphAdapter.render($("graphCanvas"), g, { onNodeClick: (node) => { $("graphDetail").innerHTML = `<h3>${escapeHtml(node.label || node.id)}</h3><p>${escapeHtml(node.summary || "暂无摘要")}</p><code>${escapeHtml(node.page_id || node.id)}</code><button class="button primary full" onclick="route('${pageLink(node.page_id || node.id)}')">打开页面</button>`; } });
    draw(graph);
    $("graphFilterBtn").onclick = () => {
      const q = $("graphQuery").value.trim().toLowerCase(), type = $("graphType").value;
      const nodes = graph.nodes.filter((n) => (!q || `${n.label} ${n.id} ${n.summary}`.toLowerCase().includes(q)) && (!type || String(n.type).toLowerCase() === type));
      const ids = new Set(nodes.map((n) => n.id));
      draw({ ...graph, nodes, edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)) });
    };
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("图谱读取失败。")}`, "", { title: "知识图谱" });
  }
}

async function renderBackend() {
  renderFrame(loadingView("正在加载后台中心..."), "", { title: "后台中心" });
  try {
    const overview = await callAction("wiki_backend_overview", { query: "", limit: 80, include_disabled: true });
    const rows = overview.rows || [], stats = overview.stats || {};
    const main = `<section class="admin-metrics">${metric("页面", stats.total ?? rows.length)}${metric("需更新", stats.update_required ?? 0)}${metric("问题", stats.issue ?? 0)}${metric("草稿", stats.draft ?? 0)}${metric("锁定", stats.locked ?? 0)}${metric("禁用", stats.disabled ?? 0)}</section><section class="panel admin-actions"><h3>全仓操作</h3><button class="button primary" onclick="adminAction('wiki_refresh_index',{extract_graph:true})">全库刷新索引</button><button class="button ghost" onclick="adminAction('wiki_batch_governance',{page_ids:adminPageIds(),operation:'diagnose'})">全库诊断</button><button class="button ghost" onclick="adminAction('wiki_batch_governance',{page_ids:adminPageIds(),operation:'check_update'})">全库检查依赖</button><pre id="adminOutput"></pre></section><section class="panel"><h3>排序表</h3><div class="admin-table">${rows.slice(0, 60).map((r) => `<div class="admin-row"><a href="${pageLink(pageIdOf(r))}">${escapeHtml(titleOf(r))}</a><span>${escapeHtml(entityTypeOf(r))}</span>${compactStatus(statusOf(r))}</div>`).join("")}</div></section>`;
    renderFrame(main, "", { title: "后台中心", subtitle: "全库统计、排序表和一键全仓管理。" });
    window._adminRows = rows;
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("后台中心加载失败。")}`, "", { title: "后台中心" });
  }
}
function adminPageIds() { return (window._adminRows || []).map(pageIdOf).filter(Boolean).slice(0, 30); }
async function adminAction(action, payload) {
  try { $("adminOutput").textContent = JSON.stringify(await callAction(action, payload), null, 2); }
  catch (e) { $("adminOutput").textContent = String(e.message || e); }
}

async function renderUser() {
  renderFrame(loadingView("正在加载用户中心..."), "", { title: "用户中心" });
  await loadUserTree("");
}
async function loadUserTree(path = state.userPath) {
  state.userPath = path || "";
  try {
    const tree = await callAction("wiki_user_file_tree", { relative_path: state.userPath });
    const main = `<section class="user-center-v31">
      <div class="cloud-panel">
        <div class="section-title"><h3>用户文件库</h3><span>${escapeHtml(tree.relative_path || "/")}</span></div>
        <div class="file-actions"><input id="newFolderName" placeholder="新文件夹名" /><button class="button ghost" onclick="createUserFolder()">新建文件夹</button><input id="uploadFileInput" type="file" /><button class="button ghost" onclick="uploadUserFile()">上传文本文件</button></div>
        <div class="file-tree">${tree.relative_path ? `<button class="file-row folder" onclick="loadUserTree('${escapeJs(parentPath(tree.relative_path))}')">⬆ 返回上级</button>` : ""}${tree.items.map(renderFileRow).join("") || emptyView("用户文件库为空。")}</div>
      </div>
      <div class="cloud-panel">
        <h3>文件内容 / 建页预览</h3>
        <textarea id="userFileEditor" placeholder="选择文件后可编辑内容；也可输入新文件路径后保存。"></textarea>
        <div class="file-actions"><input id="saveFilePath" placeholder="相对路径，例如 notes/wiki.md" value="${escapeHtml(state.userCurrentFile)}" /><button class="button primary" onclick="saveUserFile()">保存文件</button><button class="button ghost" onclick="deleteUserFile()">删除当前文件</button></div>
        <h3>用户请求与治理反馈</h3>
        <textarea id="userRequest" placeholder="例如：我刚上传了这些资料，请帮我预览哪些目录应该生成 wiki.md，并说明原因。"></textarea>
        <div class="file-actions"><button class="button primary" onclick="previewUserFolder()">预览建页</button><button class="button ghost" onclick="generateUserFolder()">确认生成 wiki.md</button></div>
        <pre id="userOutput"></pre>
      </div>
    </section>`;
    renderFrame(main, "", { title: "用户中心", subtitle: "固定用户文件库 + 类云盘小窗 + 用户请求与治理反馈。" });
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("用户文件库加载失败。")}`, "", { title: "用户中心" });
  }
}
function parentPath(path) { const parts = String(path || "").split("/").filter(Boolean); parts.pop(); return parts.join("/"); }
function renderFileRow(item) {
  const icon = item.type === "folder" ? "📁" : "📄";
  const open = item.type === "folder" ? `loadUserTree('${escapeJs(item.relative_path)}')` : `readUserFile('${escapeJs(item.relative_path)}')`;
  return `<button class="file-row ${item.type}" onclick="${open}"><span>${icon} ${escapeHtml(item.name)}</span><small>${escapeHtml(item.modified || "")}</small></button>`;
}
async function readUserFile(path) {
  try {
    const data = await callAction("wiki_user_file_read", { relative_path: path });
    state.userCurrentFile = path;
    $("userFileEditor").value = data.content || "";
    $("saveFilePath").value = path;
    $("userOutput").textContent = `已读取：${path}`;
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}
async function saveUserFile() {
  try {
    const path = $("saveFilePath").value.trim();
    const data = await callAction("wiki_user_file_write", { relative_path: path, content: $("userFileEditor").value });
    state.userCurrentFile = path;
    $("userOutput").textContent = JSON.stringify(data, null, 2);
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}
async function createUserFolder() {
  try {
    const name = $("newFolderName").value.trim();
    const rel = [state.userPath, name].filter(Boolean).join("/");
    $("userOutput").textContent = JSON.stringify(await callAction("wiki_user_file_mkdir", { relative_path: rel }), null, 2);
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}
async function uploadUserFile() {
  const file = $("uploadFileInput").files[0];
  if (!file) return;
  const text = await file.text();
  const rel = [state.userPath, file.name].filter(Boolean).join("/");
  $("saveFilePath").value = rel;
  $("userFileEditor").value = text;
  await saveUserFile();
}
async function deleteUserFile() {
  try {
    const path = $("saveFilePath").value.trim();
    $("userOutput").textContent = JSON.stringify(await callAction("wiki_user_file_delete", { relative_path: path }), null, 2);
    state.userCurrentFile = "";
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}
async function previewUserFolder() {
  try { $("userOutput").textContent = JSON.stringify(await callAction("wiki_preview_user_folder_wikis", { root_path: "user_files", author: "wiki_app" }), null, 2); }
  catch (e) { $("userOutput").textContent = String(e.message || e); }
}
async function generateUserFolder() {
  try { $("userOutput").textContent = JSON.stringify(await callAction("wiki_generate_user_folder_wikis", { root_path: "user_files", dry_run: false, author: "wiki_app" }), null, 2); }
  catch (e) { $("userOutput").textContent = String(e.message || e); }
}

function renderCurrentRoute() {
  const hash = location.hash || "#/";
  const decoded = (value) => decodeURIComponent(value || "");
  if (hash.startsWith("#/page/")) return renderPage(decoded(hash.slice("#/page/".length)));
  if (hash.startsWith("#/search")) return renderSearch(true);
  if (hash.startsWith("#/graph")) return renderGraph();
  if (hash.startsWith("#/backend")) return renderBackend();
  if (hash.startsWith("#/user")) return renderUser();
  return renderHome();
}
async function boot() {
  try { state.status = await callAction("wiki_server_status", {}); }
  catch (error) { setNotice("", `后端连接失败：${String(error.message || error)}`); }
  renderCurrentRoute();
}
window.addEventListener("hashchange", renderCurrentRoute);
boot().catch(showFatal);
