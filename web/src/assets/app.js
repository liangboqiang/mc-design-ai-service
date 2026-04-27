const $ = (id) => document.getElementById(id);

window.addEventListener("error", (event) => showFatal(event.error || event.message));
window.addEventListener("unhandledrejection", (event) => showFatal(event.reason));

function showFatal(error) {
  const root = $("root") || document.body;
  root.innerHTML = `<main class="fatal"><h1>Memory-Native Workbench 启动失败</h1><pre>${escapeHtml(String(error?.stack || error || "未知错误"))}</pre></main>`;
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
function pageIdOf(row) { return firstText(row, ["page_id", "note_id", "id", "path", "key"], ""); }
function titleOf(row) { return firstText(row, ["title", "name", "label", "page_id", "note_id", "id"], "未命名项"); }
function summaryOf(row) { return firstText(row, ["summary", "abstract", "content", "snippet", "description"], "暂无摘要。"); }
function statusOf(row) { return row?.status || { status_labels: [{ type: "ok", label: "正常", pane: "overview" }], risk_level: "none", entity_type: firstText(row, ["entity_type", "type", "kind"], "页面") }; }
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
          <div class="brand-mark">M</div>
          <div><strong>Memory-Native Workbench</strong><span>Kernel / Memory / Capability / Workbench</span></div>
        </div>
        <nav class="nav-flat">
          <a href="#/" data-nav="home">首页</a>
          <a href="#/intake" data-nav="intake">Intake</a>
          <a href="#/notes" data-nav="notes">Notes</a>
          <a href="#/review" data-nav="review">Review</a>
          <a href="#/graph" data-nav="graph">Graph</a>
          <a href="#/runtime-preview" data-nav="runtime-preview">Runtime Preview</a>
          <a href="#/tests" data-nav="tests">Tests</a>
          <a href="#/search" data-nav="search">Legacy Search</a>
          <a href="#/backend" data-nav="backend">Legacy Backend</a>
          <a href="#/user" data-nav="user">User Files</a>
        </nav>
      </aside>
      <main class="main-area">
        <div class="workspace-head ${isHome ? "home-head" : ""}">
          <div class="head-copy"><h1>${escapeHtml(options.title || titleForRoute())}</h1><p>${escapeHtml(options.subtitle || "Memory-Native Agent Workbench")}</p></div>
          ${command ? `<div class="head-command">${command}</div>` : ""}
          ${state.status ? `<div class="small-metrics"><span>项</span><strong>${state.status.catalog_count ?? state.status.memory_catalog_count ?? 0}</strong></div>` : ""}
        </div>
        ${notice()}
        <div class="${pane ? "two-column" : "single-column"}">
          <section id="contentColumn" class="content-column">${main}</section>
          ${pane ? `<aside id="contextPane" class="context-pane">${pane}</aside>` : ""}
        </div>
      </main>
    </div>`;
  markActiveNav();
}

function titleForRoute() {
  const hash = location.hash || "#/";
  if (hash.startsWith("#/intake")) return "Intake";
  if (hash.startsWith("#/notes")) return "Notes";
  if (hash.startsWith("#/review")) return "Review";
  if (hash.startsWith("#/page/")) return "页面详情";
  if (hash.startsWith("#/search")) return "Legacy Search";
  if (hash.startsWith("#/graph")) return "Graph";
  if (hash.startsWith("#/runtime-preview")) return "Runtime Preview";
  if (hash.startsWith("#/tests")) return "Tests";
  if (hash.startsWith("#/backend")) return "Legacy Backend";
  if (hash.startsWith("#/user")) return "User Files";
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

function searchCommand() {
  return `<div class="compact-command search-command"><input id="searchQueryInput" value="${escapeHtml(state.query)}" placeholder="搜索页面、工具、Skill、Agent、文件、关系..." /><button id="searchRunBtn" class="button primary icon-btn" title="搜索">🔎</button><button id="searchRefreshBtn" class="button ghost icon-btn" title="刷新索引">↻</button></div>`;
}

function pageCommand(pageId = "") {
  return `<div class="compact-command page-command"><input id="pageSearchInput" placeholder="在阅读中继续搜索..." /><button id="pageSearchBtn" class="button primary icon-btn" title="搜索">🔎</button><button id="pageBackSearchBtn" class="button ghost icon-btn" title="返回搜索" onclick="route('#/search')">↩</button></div>`;
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
function optionList(map, current) { return Object.entries(map).map(([value, label]) => `<option value="${escapeHtml(value)}" ${value === current ? "selected" : ""}>${escapeHtml(label)}</option>`).join(""); }
function infoIcon(k) { return ({ "实体类型": "⌁", "页面 ID": "#", "阶段": "◷", "锁定": "🔒", "禁用": "⊘", "作用范围": "⌖", "风险等级": "⚠", "问题数量": "!", "变化文件": "↻", "草稿数量": "✎" })[k] || "•"; }
function infoRow(k, v) { return `<div class="info-row" title="${escapeHtml(k)}"><span class="info-icon">${infoIcon(k)}</span><strong>${escapeHtml(v)}</strong></div>`; }

function bindSearchCommand() {
  $("searchRunBtn").onclick = () => {
    state.query = $("searchQueryInput").value.trim();
    route(`#/search?q=${encodeURIComponent(state.query)}`);
    renderSearch();
  };
  $("searchQueryInput").onkeydown = (e) => { if (e.key === "Enter") $("searchRunBtn").click(); };
  $("searchRefreshBtn").onclick = refreshIndex;
}

function bindPageCommand() {
  $("pageSearchBtn").onclick = () => {
    state.query = $("pageSearchInput").value.trim();
    route(`#/search?q=${encodeURIComponent(state.query)}`);
    renderSearch();
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

async function renderHome() { return window.WikiWorkbenchPages.renderHome(); }
async function renderSearch() { return window.WikiWorkbenchPages.renderSearch(); }
async function renderPage(pageId, pane = state.currentPane || "overview") { return window.WikiWorkbenchPages.renderPage(pageId, pane); }
async function renderGraph() { return window.WikiWorkbenchPages.renderGraph(); }
async function renderBackend() { return window.WikiWorkbenchPages.renderBackend(); }
async function renderUser() { return window.WikiWorkbenchPages.renderUser(); }
async function renderNotes() { return window.WikiWorkbenchPages.renderNotes(); }
async function renderReview() { return window.WikiWorkbenchPages.renderReview(); }
async function renderRuntimePreview() { return window.WikiWorkbenchPages.renderRuntimePreview(); }
async function renderTests() { return window.WikiWorkbenchPages.renderTests(); }
async function renderIntake() { return window.WikiWorkbenchPages.renderIntake(); }

function renderCurrentRoute() {
  const hash = location.hash || "#/";
  const decoded = (value) => decodeURIComponent(value || "");
  if (hash.startsWith("#/intake")) return renderIntake();
  if (hash.startsWith("#/notes")) return renderNotes();
  if (hash.startsWith("#/review")) return renderReview();
  if (hash.startsWith("#/page/")) return renderPage(decoded(hash.slice("#/page/".length)));
  if (hash.startsWith("#/search")) return renderSearch();
  if (hash.startsWith("#/graph")) return renderGraph();
  if (hash.startsWith("#/runtime-preview")) return renderRuntimePreview();
  if (hash.startsWith("#/tests")) return renderTests();
  if (hash.startsWith("#/backend")) return renderBackend();
  if (hash.startsWith("#/user")) return renderUser();
  return renderHome();
}

async function boot() {
  try {
    state.status = await callAction("wiki_server_status", {});
  } catch (error) {
    setNotice("", `后端连接失败：${String(error.message || error)}`);
  }
  renderCurrentRoute();
}

window.addEventListener("hashchange", renderCurrentRoute);
boot().catch(showFatal);
