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
  el.innerHTML = tags.length ? `组合词条：${tags.map((t) => `<span class="selected-tag">${escapeHtml(t)}</span>`).join("")}` : `选择下拉词条用于加工 query，不会单独触发搜索。`;
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

function renderHistoryTile(rows) {
  return `<article class="portal-tile history-tile">
    <div class="tile-head"><span class="tile-icon">🕘</span><div><h3>历史详情页</h3><small>最近可进入页面</small></div></div>
    <div class="tile-list">
      ${rows.length ? rows.map((r) => `<a href="${pageLink(pageIdOf(r))}">${escapeHtml(titleOf(r)).slice(0, 20)}<span>›</span></a>`).join("") : `<a href="#/search">进入搜索<span>›</span></a>`}
    </div>
  </article>`;
}

function renderNotesTile(notes) {
  return `<article class="portal-tile backend-tile">
    <div class="tile-head"><span class="tile-icon">▣</span><div><h3>Notes</h3><small>${notes.length} 条知识单元</small></div><a class="tile-link" href="#/notes">↗</a></div>
    <div class="dashboard-mini">
      ${notes.slice(0, 4).map((item) => metric(item.kind || "note", item.title.slice(0, 8))).join("")}
    </div>
  </article>`;
}

function renderReviewTile(proposals) {
  return `<article class="portal-tile user-tile">
    <div class="tile-head"><span class="tile-icon">◇</span><div><h3>Review</h3><small>${proposals.length} 个待审提案</small></div><a class="tile-link" href="#/review">↗</a></div>
    <div class="tile-list">
      ${proposals.length ? proposals.slice(0, 4).map((item) => `<a href="#/review?id=${escapeHtml(item.proposal_id)}">${escapeHtml(item.proposal_type || item.proposal_id)}<span>›</span></a>`).join("") : `<a href="#/review">进入审核中心<span>›</span></a>`}
    </div>
  </article>`;
}

function renderGraphTile(graph) {
  const n = (graph.nodes || []).length || 0;
  const e = (graph.edges || []).length || 0;
  return `<article class="portal-tile graph-tile">
    <div class="tile-head"><span class="tile-icon">◎</span><div><h3>Memory Graph</h3><small>${n} 节点 · ${e} 关系</small></div><a class="tile-link" href="#/graph">↗</a></div>
    <div id="homeGraphMini" class="home-graph-mini"></div>
  </article>`;
}

function renderRuntimeTile() {
  return `<article class="portal-tile history-tile">
    <div class="tile-head"><span class="tile-icon">⟳</span><div><h3>Runtime Preview</h3><small>查看 Prompt / Memory / Capability</small></div><a class="tile-link" href="#/runtime-preview">↗</a></div>
    <div class="tile-list">
      <a href="#/runtime-preview">预览 MemoryView<span>›</span></a>
      <a href="#/runtime-preview">预览 CapabilityView<span>›</span></a>
      <a href="#/tests">进入测试中心<span>›</span></a>
    </div>
  </article>`;
}

function renderUserTile() {
  return `<article class="portal-tile user-tile">
    <div class="tile-head"><span class="tile-icon">◌</span><div><h3>User Files</h3><small>文件与治理反馈</small></div><a class="tile-link" href="#/user">↗</a></div>
    <div class="user-chat-mini">
      <div class="chat-bubble">导入资料后，可从 Intake / User Files 进入 Memory 流程。</div>
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

async function renderHomeImpl() {
  renderFrame(loadingView("正在加载首页..."), "", { title: "首页", subtitle: "Memory-Native Agent Workbench" });
  try {
    state.status = await callAction("wiki_server_status", {});
    const [notes, graph, proposals, overview] = await Promise.all([
      callMemoryAction("memory_list_notes", { limit: 8 }).catch(() => []),
      callMemoryAction("memory_graph_view", { include_hidden: false }).catch(() => ({ nodes: [], edges: [] })),
      callMemoryAction("memory_list_proposals", { status: "candidate" }).catch(() => []),
      callAction("wiki_backend_overview", { query: "", limit: 8, include_disabled: false }).catch(() => ({ rows: [], stats: {} })),
    ]);
    const rows = overview.rows || [];
    const recent = rows.slice(0, 4);
    const main = `
      <section class="home-hero-card">
        <div class="hero-copy">
          <h2>Memory-Native Agent 总览</h2>
          <p>首页主导航已切换到 Notes / Review / Graph / Runtime Preview，旧 Wiki 搜索作为兼容入口保留。</p>
        </div>
        ${homeSearchPanel()}
      </section>
      <section class="home-tile-grid">
        ${renderHistoryTile(recent)}
        ${renderNotesTile(notes)}
        ${renderReviewTile(proposals)}
        ${renderGraphTile(normalizeGraphData(graph))}
        ${renderRuntimeTile()}
        ${renderUserTile()}
      </section>`;
    renderFrame(main, "", { title: "首页", subtitle: "Kernel / Memory / Capability / Workbench", command: "" });
    bindHomeSearchPanel();
    drawHomeGraphMini(graph);
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("首页加载失败。")}`, "", { title: "首页" });
  }
}

window.WikiWorkbenchPages.renderHome = renderHomeImpl;
