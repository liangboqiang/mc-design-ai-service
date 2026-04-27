async function runWorkbenchTest() {
  const task = $("testTaskInput")?.value?.trim() || state.testTask;
  state.testTask = task;
  renderFrame(loadingView("正在执行测试..."), "", { title: "Tests", subtitle: task });
  try {
    const data = await callMemoryAction("memory_run_test_case", { task });
    const main = `<section class="panel"><h3>Test Task</h3><textarea id="testTaskInput">${escapeHtml(task)}</textarea><div class="pane-action-grid"><button id="testRunBtn" class="button primary">重新执行</button></div></section><section class="panel"><h3>Result</h3><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></section>`;
    renderFrame(main, "", { title: "Tests", subtitle: "固定任务回归入口" });
    if ($("testRunBtn")) $("testRunBtn").onclick = runWorkbenchTest;
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}<section class="panel"><textarea id="testTaskInput">${escapeHtml(task)}</textarea><div class="pane-action-grid"><button id="testRunBtn" class="button primary">重新执行</button></div></section>`, "", { title: "Tests" });
    if ($("testRunBtn")) $("testRunBtn").onclick = runWorkbenchTest;
  }
}

async function renderTestsImpl() {
  renderFrame(`<section class="panel"><h3>Regression Task</h3><textarea id="testTaskInput">${escapeHtml(state.testTask)}</textarea><div class="pane-action-grid"><button id="testRunBtn" class="button primary">执行测试</button></div></section>`, "", { title: "Tests", subtitle: "Memory / Capability / Prompt 闭环测试" });
  if ($("testRunBtn")) $("testRunBtn").onclick = runWorkbenchTest;
}

window.WikiWorkbenchPages.renderTests = renderTestsImpl;
