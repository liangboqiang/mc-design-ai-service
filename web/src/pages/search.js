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

async function renderSearchImpl() {
  const params = getHashQuery();
  if (params.has("q")) state.query = params.get("q") || "";
  renderFrame(loadingView("正在检索..."), renderSearchPane(), { title: "Legacy Search", subtitle: "旧 Wiki 检索入口保留为兼容视图。", command: searchCommand() });
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
    let rows = data.results || [];
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
    renderFrame(`${notice()}${emptyView("搜索失败。")}`, renderSearchPane(), { title: "Legacy Search", command: searchCommand() });
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
  renderFrame(main, renderSearchPane(), { title: "Legacy Search", subtitle: `${state.results.length} 条结果`, command: searchCommand() });
  bindSearchCommand();
  wireSearchControls();
  wireResultCards();
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
  $("applyFiltersBtn").onclick = () => renderSearch();
  $("selectAllResults").onchange = (e) => {
    state.results.forEach((r) => { const id = pageIdOf(r); if (id) e.target.checked ? state.selected.add(id) : state.selected.delete(id); });
    syncSelectionUi();
  };
}

function wireResultCards() {
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
  return `<div class="pane-card"><h3>搜索上下文</h3><p>Legacy 搜索结果可继续进入旧页面治理流；新 Workbench 入口请使用 Notes / Review / Runtime Preview。</p><div class="pane-action-grid"><button class="button ghost" onclick="selectAllVisible()">全选当前结果</button><button class="button ghost" onclick="state.filters.only_governance=true; renderSearch()">仅看待治理</button><button class="button ghost" onclick="route('#/notes')">切换到 Notes</button></div></div>`;
}

function selectAllVisible() {
  state.results.forEach((r) => { const id = pageIdOf(r); if (id) state.selected.add(id); });
  syncSelectionUi();
}

function renderResultContextPane(pageId) {
  const row = state.results.find((r) => pageIdOf(r) === pageId) || {};
  const status = statusOf(row);
  return `<div class="pane-card"><h3>${escapeHtml(titleOf(row))}</h3>${compactStatus(status)}<p>${escapeHtml(summaryOf(row))}</p><code>${escapeHtml(pageId)}</code><div class="pane-action-grid"><button class="button primary" onclick="route('${pageLink(pageId)}')">打开页面</button><button class="button ghost" onclick="runPaneAction('wiki_page_status_summary',{page_id:'${escapeJs(pageId)}'})">状态评估</button><button class="button ghost" onclick="runPaneAction('wiki_diagnose_page',{page_id:'${escapeJs(pageId)}'})">诊断页面</button></div><pre id="paneOutput"></pre></div>`;
}

function renderBatchPane() {
  const ids = [...state.selected];
  return `<div class="pane-card batch-pane"><h3>批量治理流程</h3><p>已选 ${ids.length} 个页面。</p>
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

window.WikiWorkbenchPages.renderSearch = renderSearchImpl;
