async function renderUserImpl() {
  renderFrame(loadingView("正在加载用户中心..."), "", { title: "User Files" });
  await loadUserTree("");
}

async function loadUserTree(path = state.userPath) {
  state.userPath = path || "";
  try {
    const tree = await callAction("wiki_user_file_tree", { relative_path: state.userPath });
    const main = `<section class="user-center-v31">
      <div class="cloud-panel">
        <div class="section-title"><h3>用户文件库</h3><span>${escapeHtml(tree.relative_path || "/")}</span></div>
        <div class="file-actions"><input id="newFolderName" placeholder="新文件夹名" /><button class="button ghost" onclick="createUserFolder()">新建文件夹</button><input id="uploadFileInput" type="file" /><button class="button ghost" onclick="uploadUserFile()">上传文本文件</button></div>
        <div class="file-tree">${tree.relative_path ? `<button class="file-row folder" onclick="loadUserTree('${escapeJs(parentPath(tree.relative_path))}')">⬆ 返回上级</button>` : ""}${tree.items.map(renderFileRow).join("") || emptyView("用户文件库为空。")}</div>
      </div>
      <div class="cloud-panel">
        <h3>文件内容 / 建页预览</h3>
        <textarea id="userFileEditor" placeholder="选择文件后可编辑内容；也可输入新文件路径后保存。"></textarea>
        <div class="file-actions"><input id="saveFilePath" placeholder="相对路径，例如 notes/wiki.md" value="${escapeHtml(state.userCurrentFile)}" /><button class="button primary" onclick="saveUserFile()">保存文件</button><button class="button ghost" onclick="deleteUserFile()">删除当前文件</button></div>
        <h3>用户请求与治理反馈</h3>
        <textarea id="userRequest" placeholder="例如：我刚上传了这些资料，请帮我预览哪些目录应该生成 note.md，并说明原因。"></textarea>
        <div class="file-actions"><button class="button primary" onclick="previewUserFolder()">预览建页</button><button class="button ghost" onclick="generateUserFolder()">确认生成兼容页面</button></div>
        <pre id="userOutput"></pre>
      </div>
    </section>`;
    renderFrame(main, "", { title: "User Files", subtitle: "兼容旧用户文件流" });
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("用户文件库加载失败。")}`, "", { title: "User Files" });
  }
}

function parentPath(path) { const parts = String(path || "").split("/").filter(Boolean); parts.pop(); return parts.join("/"); }

function renderFileRow(item) {
  const icon = item.type === "folder" ? "📁" : "📄";
  const open = item.type === "folder" ? `loadUserTree('${escapeJs(item.relative_path)}')` : `readUserFile('${escapeJs(item.relative_path)}')`;
  return `<button class="file-row ${item.type}" onclick="${open}"><span>${icon} ${escapeHtml(item.name)}</span><small>${escapeHtml(item.modified || "")}</small></button>`;
}

async function readUserFile(path) {
  try {
    const data = await callAction("wiki_user_file_read", { relative_path: path });
    state.userCurrentFile = path;
    $("userFileEditor").value = data.content || "";
    $("saveFilePath").value = path;
    $("userOutput").textContent = `已读取：${path}`;
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}

async function saveUserFile() {
  try {
    const path = $("saveFilePath").value.trim();
    const data = await callAction("wiki_user_file_write", { relative_path: path, content: $("userFileEditor").value });
    state.userCurrentFile = path;
    $("userOutput").textContent = JSON.stringify(data, null, 2);
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}

async function createUserFolder() {
  try {
    const name = $("newFolderName").value.trim();
    const rel = [state.userPath, name].filter(Boolean).join("/");
    $("userOutput").textContent = JSON.stringify(await callAction("wiki_user_file_mkdir", { relative_path: rel }), null, 2);
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}

async function uploadUserFile() {
  const file = $("uploadFileInput").files[0];
  if (!file) return;
  const text = await file.text();
  const rel = [state.userPath, file.name].filter(Boolean).join("/");
  $("saveFilePath").value = rel;
  $("userFileEditor").value = text;
  await saveUserFile();
}

async function deleteUserFile() {
  try {
    const path = $("saveFilePath").value.trim();
    $("userOutput").textContent = JSON.stringify(await callAction("wiki_user_file_delete", { relative_path: path }), null, 2);
    state.userCurrentFile = "";
    await loadUserTree(state.userPath);
  } catch (e) { $("userOutput").textContent = String(e.message || e); }
}

async function previewUserFolder() {
  try { $("userOutput").textContent = JSON.stringify(await callAction("wiki_preview_user_folder_wikis", { root_path: "user_files", author: "wiki_app" }), null, 2); }
  catch (e) { $("userOutput").textContent = String(e.message || e); }
}

async function generateUserFolder() {
  try { $("userOutput").textContent = JSON.stringify(await callAction("wiki_generate_user_folder_wikis", { root_path: "user_files", dry_run: false, author: "wiki_app" }), null, 2); }
  catch (e) { $("userOutput").textContent = String(e.message || e); }
}

window.WikiWorkbenchPages.renderUser = renderUserImpl;
