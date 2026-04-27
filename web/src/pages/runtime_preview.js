function runtimePreviewCommand() {
  return `<div class="compact-command"><button id="runtimeRunBtn" class="button primary">运行预览</button></div>`;
}

async function runRuntimePreview() {
  const task = $("runtimeTaskInput")?.value?.trim() || state.runtimeTask;
  state.runtimeTask = task;
  renderFrame(loadingView("正在生成 runtime preview..."), "", { title: "Runtime Preview", subtitle: task, command: runtimePreviewCommand() });
  try {
    const data = await callMemoryAction("memory_preview_runtime", { task });
    const main = `<section class="panel"><h3>Task</h3><textarea id="runtimeTaskInput">${escapeHtml(task)}</textarea><div class="pane-action-grid"><button id="runtimeRunBtn2" class="button primary">重新预览</button></div></section><section class="panel"><h3>MemoryView</h3><pre>${escapeHtml(JSON.stringify(data.memory_view, null, 2))}</pre></section><section class="panel"><h3>CapabilityView</h3><pre>${escapeHtml(JSON.stringify(data.capability_view, null, 2))}</pre></section><section class="panel"><h3>Prompt</h3><pre>${escapeHtml(data.prompt || "")}</pre></section><section class="panel"><h3>Runtime Ready Checks</h3><pre>${escapeHtml(JSON.stringify(data.runtime_ready_checks || [], null, 2))}</pre></section>`;
    renderFrame(main, "", { title: "Runtime Preview", subtitle: "MemoryView + CapabilityView + Prompt", command: runtimePreviewCommand() });
    if ($("runtimeRunBtn")) $("runtimeRunBtn").onclick = runRuntimePreview;
    if ($("runtimeRunBtn2")) $("runtimeRunBtn2").onclick = runRuntimePreview;
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}<section class="panel"><textarea id="runtimeTaskInput">${escapeHtml(task)}</textarea><div class="pane-action-grid"><button id="runtimeRunBtn" class="button primary">重新预览</button></div></section>`, "", { title: "Runtime Preview", command: runtimePreviewCommand() });
    if ($("runtimeRunBtn")) $("runtimeRunBtn").onclick = runRuntimePreview;
  }
}

async function renderRuntimePreviewImpl() {
  renderFrame(`<section class="panel"><h3>Runtime Task</h3><textarea id="runtimeTaskInput">${escapeHtml(state.runtimeTask)}</textarea><div class="pane-action-grid"><button id="runtimeRunBtn" class="button primary">运行预览</button></div></section>`, "", { title: "Runtime Preview", subtitle: "预览 Observe / Orient / Capability / Prompt", command: runtimePreviewCommand() });
  if ($("runtimeRunBtn")) $("runtimeRunBtn").onclick = runRuntimePreview;
}

window.WikiWorkbenchPages.renderRuntimePreview = renderRuntimePreviewImpl;
