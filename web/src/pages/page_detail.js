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

async function renderPageImpl(pageId, pane = state.currentPane || "overview") {
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
    renderFrame(main, renderPagePane(pane, { pageId, info, status, hint, diagnosis }), { title: "页面详情", subtitle: "Legacy 详情页兼容视图", command: pageCommand(pageId) });
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

window.WikiWorkbenchPages.renderPage = renderPageImpl;
