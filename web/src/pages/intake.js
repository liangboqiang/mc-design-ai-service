async function runIntakeUpload() {
  const files = [...($("intakeFiles")?.files || [])];
  if (!files.length) {
    setNotice("", "请先选择文件。");
    renderIntake();
    return;
  }
  const payload = [];
  for (const file of files) {
    payload.push({ name: file.name, content: await file.text() });
  }
  renderFrame(loadingView("正在导入 Evidence..."), "", { title: "Intake" });
  try {
    const data = await callMemoryAction("memory_ingest_source", { files: payload });
    renderFrame(`<section class="panel"><h3>Evidence Intake</h3><input id="intakeFiles" type="file" multiple /><div class="pane-action-grid"><button id="intakeUploadBtn" class="button primary">继续导入</button></div></section><section class="panel"><h3>Ingest Result</h3><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre></section>`, "", { title: "Intake", subtitle: "文件已进入 EvidenceStore" });
    if ($("intakeUploadBtn")) $("intakeUploadBtn").onclick = runIntakeUpload;
  } catch (error) {
    setNotice("", String(error.message || error));
    renderIntake();
  }
}

async function renderIntakeImpl() {
  renderFrame(`<section class="panel"><h3>Evidence Intake</h3><p>上传文本资料后会直接写入 EvidenceStore，并作为 Proposal / Note 的来源。</p><input id="intakeFiles" type="file" multiple /><div class="pane-action-grid"><button id="intakeUploadBtn" class="button primary">导入文件</button></div></section>`, "", { title: "Intake", subtitle: "上传 -> Evidence -> Proposal -> Review" });
  if ($("intakeUploadBtn")) $("intakeUploadBtn").onclick = runIntakeUpload;
}

window.WikiWorkbenchPages.renderIntake = renderIntakeImpl;
