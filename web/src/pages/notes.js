function notesCommand() {
  return `<div class="compact-command search-command"><input id="noteQueryInput" value="${escapeHtml(state.noteQuery)}" placeholder="搜索 note / kind / path..." /><button id="noteSearchBtn" class="button primary icon-btn" title="搜索">🔎</button><button id="noteClearBtn" class="button ghost icon-btn" title="清空">↺</button></div>`;
}

function bindNotesCommand() {
  $("noteSearchBtn").onclick = () => {
    state.noteQuery = $("noteQueryInput").value.trim();
    route(`#/notes?q=${encodeURIComponent(state.noteQuery)}`);
    renderNotes();
  };
  $("noteClearBtn").onclick = () => {
    state.noteQuery = "";
    route("#/notes");
    renderNotes();
  };
  $("noteQueryInput").onkeydown = (e) => { if (e.key === "Enter") $("noteSearchBtn").click(); };
}

function renderNoteCard(note) {
  const active = state.selectedNoteId === note.note_id ? "active" : "";
  return `<article class="search-card ${active}" onclick="openNote('${escapeJs(note.note_id)}')"><div class="search-card-main"><div class="search-title-line"><strong class="result-title">${escapeHtml(note.title)}</strong><span class="entity-pill">${escapeHtml(note.kind)}</span></div><p>${escapeHtml(note.summary || "暂无摘要")}</p><code>${escapeHtml(note.note_id)}</code><div class="matched-reason">${escapeHtml(note.status)} · ${escapeHtml(note.maturity || "")}</div></div></article>`;
}

function openNote(noteId) {
  state.selectedNoteId = noteId;
  const q = state.noteQuery ? `?q=${encodeURIComponent(state.noteQuery)}&note=${encodeURIComponent(noteId)}` : `?note=${encodeURIComponent(noteId)}`;
  route(`#/notes${q}`);
  renderNotes();
}

function renderNotePane(note, check) {
  if (!note) return `<div class="pane-card"><h3>Note Detail</h3><p>请选择左侧 note。</p></div>`;
  const diagnostics = check?.diagnostics || [];
  return `<div class="pane-card"><h3>${escapeHtml(note.title)}</h3><div class="info-row"><span class="info-icon">#</span><strong>${escapeHtml(note.note_id)}</strong></div><div class="info-row"><span class="info-icon">⌁</span><strong>${escapeHtml(note.kind)}</strong></div><div class="info-row"><span class="info-icon">◷</span><strong>${escapeHtml(note.status)} / ${escapeHtml(note.maturity || "")}</strong></div><div class="pane-action-grid"><button class="button ghost" onclick="route('${pageLink(note.note_id)}')">用兼容详情打开</button></div><h3>Normalized Fields</h3><pre>${escapeHtml(JSON.stringify(check?.normalized_fields || {}, null, 2))}</pre><h3>Diagnostics</h3><pre>${escapeHtml(JSON.stringify(diagnostics, null, 2))}</pre></div>`;
}

async function renderNotesImpl() {
  const params = getHashQuery();
  if (params.has("q")) state.noteQuery = params.get("q") || "";
  if (params.has("note")) state.selectedNoteId = params.get("note") || "";
  renderFrame(loadingView("正在读取 notes..."), loadingView("准备 detail..."), { title: "Notes", subtitle: "MemoryNote 浏览与诊断", command: notesCommand() });
  bindNotesCommand();
  try {
    const notes = await callMemoryAction("memory_list_notes", { query: state.noteQuery, limit: 120 });
    if (!state.selectedNoteId && notes[0]) state.selectedNoteId = notes[0].note_id;
    const selected = notes.find((item) => item.note_id === state.selectedNoteId) || notes[0] || null;
    const check = selected ? await callMemoryAction("memory_check_note", { note_id: selected.note_id }) : null;
    const main = `<section class="panel"><h3>Notes Catalog</h3><div class="results-list">${notes.map(renderNoteCard).join("") || emptyView("暂无 note")}</div></section>`;
    renderFrame(main, renderNotePane(selected, check), { title: "Notes", subtitle: `${notes.length} 条 note`, command: notesCommand() });
    bindNotesCommand();
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("Notes 加载失败。")}`, "", { title: "Notes", command: notesCommand() });
    bindNotesCommand();
  }
}

window.WikiWorkbenchPages.renderNotes = renderNotesImpl;
