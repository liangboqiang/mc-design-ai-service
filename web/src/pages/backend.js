async function renderBackendImpl() {
  renderFrame(loadingView("正在加载后台中心..."), "", { title: "Legacy Backend" });
  try {
    const overview = await callAction("wiki_backend_overview", { query: "", limit: 80, include_disabled: true });
    const rows = overview.rows || [], stats = overview.stats || {};
    const main = `<section class="admin-metrics">${metric("页面", stats.total ?? rows.length)}${metric("需更新", stats.update_required ?? 0)}${metric("问题", stats.issue ?? 0)}${metric("草稿", stats.draft ?? 0)}${metric("锁定", stats.locked ?? 0)}${metric("禁用", stats.disabled ?? 0)}</section><section class="panel admin-actions"><h3>全仓操作</h3><button class="button primary" onclick="adminAction('wiki_refresh_index',{extract_graph:true})">全库刷新索引</button><button class="button ghost" onclick="adminAction('wiki_batch_governance',{page_ids:adminPageIds(),operation:'diagnose'})">全库诊断</button><button class="button ghost" onclick="adminAction('wiki_batch_governance',{page_ids:adminPageIds(),operation:'check_update'})">全库检查依赖</button><pre id="adminOutput"></pre></section><section class="panel"><h3>排序表</h3><div class="admin-table">${rows.slice(0, 60).map((r) => `<div class="admin-row"><a href="${pageLink(pageIdOf(r))}">${escapeHtml(titleOf(r))}</a><span>${escapeHtml(entityTypeOf(r))}</span>${compactStatus(statusOf(r))}</div>`).join("")}</div></section>`;
    renderFrame(main, "", { title: "Legacy Backend", subtitle: "兼容旧 Wiki 全仓看板" });
    window._adminRows = rows;
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("后台中心加载失败。")}`, "", { title: "Legacy Backend" });
  }
}

function adminPageIds() { return (window._adminRows || []).map(pageIdOf).filter(Boolean).slice(0, 30); }

async function adminAction(action, payload) {
  try { $("adminOutput").textContent = JSON.stringify(await callAction(action, payload), null, 2); }
  catch (e) { $("adminOutput").textContent = String(e.message || e); }
}

window.WikiWorkbenchPages.renderBackend = renderBackendImpl;
