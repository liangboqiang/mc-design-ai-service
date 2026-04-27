function reviewCommand() {
  return `<div class="compact-command search-command"><select id="proposalStatus"><option value="candidate">candidate</option><option value="reviewed">reviewed</option><option value="accepted">accepted</option><option value="rejected">rejected</option></select><button id="proposalReloadBtn" class="button primary icon-btn">↻</button></div>`;
}

function bindReviewCommand() {
  if ($("proposalReloadBtn")) $("proposalReloadBtn").onclick = () => renderReview();
}

function renderProposalRow(item) {
  const active = item.proposal_id === state.selectedProposalId ? "active" : "";
  return `<article class="search-card ${active}" onclick="openProposal('${escapeJs(item.proposal_id)}')"><div class="search-card-main"><div class="search-title-line"><strong class="result-title">${escapeHtml(item.proposal_type || item.proposal_id)}</strong><span class="entity-pill">${escapeHtml(item.status || "candidate")}</span></div><p>${escapeHtml(item.source || "runtime")}</p><code>${escapeHtml(item.proposal_id)}</code></div></article>`;
}

function openProposal(proposalId) {
  state.selectedProposalId = proposalId;
  route(`#/review?id=${encodeURIComponent(proposalId)}`);
  renderReview();
}

async function reviewSelectedProposal(decision) {
  if (!state.selectedProposalId) return;
  try {
    await callMemoryAction("memory_review_proposal", { proposal_id: state.selectedProposalId, decision, review_notes: `frontend:${decision}` });
    setNotice(`Proposal 已标记为 ${decision}`);
    renderReview();
  } catch (error) {
    setNotice("", String(error.message || error));
    renderReview();
  }
}

function renderProposalPane(item) {
  if (!item) return `<div class="pane-card"><h3>Proposal Detail</h3><p>暂无提案。</p></div>`;
  return `<div class="pane-card"><h3>${escapeHtml(item.proposal_id)}</h3><div class="pane-action-grid"><button class="button primary" onclick="reviewSelectedProposal('accepted')">接受</button><button class="button ghost" onclick="reviewSelectedProposal('reviewed')">标记 reviewed</button><button class="button ghost" onclick="reviewSelectedProposal('rejected')">拒绝</button></div><pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre></div>`;
}

async function renderReviewImpl() {
  const params = getHashQuery();
  if (params.has("id")) state.selectedProposalId = params.get("id") || "";
  renderFrame(loadingView("正在读取 proposals..."), loadingView("准备 detail..."), { title: "Review", subtitle: "ProposalQueue 审核入口", command: reviewCommand() });
  bindReviewCommand();
  try {
    const status = $("proposalStatus") ? $("proposalStatus").value : "candidate";
    const rows = await callMemoryAction("memory_list_proposals", { status });
    const selected = rows.find((item) => item.proposal_id === state.selectedProposalId) || rows[0] || null;
    if (selected) state.selectedProposalId = selected.proposal_id;
    const main = `<section class="panel"><h3>Proposals</h3><div class="results-list">${rows.map(renderProposalRow).join("") || emptyView("暂无 proposal")}</div></section>`;
    renderFrame(main, renderProposalPane(selected), { title: "Review", subtitle: `${rows.length} 个 proposal`, command: reviewCommand() });
    if ($("proposalStatus")) $("proposalStatus").value = status;
    bindReviewCommand();
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("Review 加载失败。")}`, "", { title: "Review", command: reviewCommand() });
    bindReviewCommand();
  }
}

window.WikiWorkbenchPages.renderReview = renderReviewImpl;
