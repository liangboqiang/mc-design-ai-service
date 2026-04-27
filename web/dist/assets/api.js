(function () {
  const BASE = '/app/action/';
  async function postJson(action, payload) {
    const response = await fetch(BASE + action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      const message = data && data.error && data.error.message ? data.error.message : ('请求失败：' + response.status);
      throw new Error(message);
    }
    return data.data;
  }
  const action = (name, payload) => postJson(name, payload);
  const api = {
    action,
    postJson,
    memory(name, payload) { return action(name, payload); },
    workbench(name, payload) { return action(name, payload); },
    note: {
      search(payload) { return action('graphpedia_search', payload); },
      read(note_id) { return action('memory_read_note_detail', { note_id }); },
      save(note_id, markdown, commit, message) { return action('memory_save_note_source', { note_id, markdown, commit: !!commit, message }); },
      proposal(note_id, markdown, proposal_type, review_notes) { return action('memory_create_note_proposal', { note_id, markdown, proposal_type: proposal_type || 'note_patch', review_notes: review_notes || '' }); },
      publish(note_id, maturity) { return action('memory_publish_note', { note_id, maturity: maturity || 'projectable' }); },
      fromFile(scope, path, target_kind, mode) { return action('memory_generate_note_from_file', { scope, path, target_kind: target_kind || 'Document', mode: mode || 'proposal' }); },
    },
    graph: {
      view(include_hidden) { return action('memory_graph_view', { include_hidden: include_hidden !== false }); },
      compile(include_hidden, write_store) { return action('memory_compile_graph', { include_hidden: include_hidden !== false, write_store: write_store !== false }); },
      neighbors(note_id, depth) { return action('memory_graph_neighbors', { note_id, depth: depth || 1 }); },
    },
    workspace: {
      roots() { return action('workspace_roots', {}); },
      list(scope, path, recursive) { return action('workspace_list_files', { scope, path: path || '', recursive: !!recursive }); },
      read(scope, path) { return action('workspace_read_file', { scope, path }); },
      write(scope, path, content) { return action('workspace_write_file', { scope, path, content }); },
      upload(scope, path, files) { return action('workspace_upload_files', { scope, path: path || '', files: files || [] }); },
      mkdir(scope, path) { return action('workspace_make_dir', { scope, path }); },
      remove(scope, path) { return action('workspace_delete_file', { scope, path }); },
      move(scope, source, target) { return action('workspace_move_file', { scope, source, target }); },
      extract(scope, path) { return action('workspace_extract_file', { scope, path }); },
      createUserSession(user_id, session_id) { return action('user_workspace_create_session', { user_id, session_id }); },
      submitUserFile(user_id, session_id, path, target) { return action('user_workspace_submit_to_team', { user_id, session_id, path, target: target || 'incoming' }); },
    },
    repo: {
      config() { return action('repo_config_read', {}); },
      saveConfig(config) { return action('repo_config_save', { config }); },
      list() { return action('repo_list', {}); },
      save(repository) { return action('repo_save', { repository }); },
      remove(repo_id) { return action('repo_delete', { repo_id }); },
    },
    notebook: {
      list() { return action('notebook_list', {}); },
      read(notebook_id) { return action('notebook_read', { notebook_id }); },
      save(notebook) { return action('notebook_save', { notebook }); },
      remove(notebook_id) { return action('notebook_delete', { notebook_id }); },
    },
    schema: {
      list() { return action('soft_schema_list', {}); },
      read(schema_id) { return action('soft_schema_read', { schema_id }); },
      save(schema) { return action('soft_schema_save', { schema }); },
      discover(schema_id, repo_id) { return action('soft_schema_discover', { schema_id, repo_id }); },
      acceptField(schema_id, field_name, config) { return action('soft_schema_accept_field', { schema_id, field_name, config: config || {} }); },
    },
    version: {
      status() { return action('version_status', {}); },
      commit(message, author, scope) { return action('version_commit_notes', { message, author, scope }); },
      commits(limit) { return action('version_list_commits', { limit: limit || 50 }); },
      history(note_id, note_path) { return action('version_note_history', { note_id: note_id || '', note_path: note_path || '' }); },
      diff(note_id, from_commit, to_commit) { return action('version_diff_note', { note_id, from_commit: from_commit || '', to_commit: to_commit || 'WORKTREE' }); },
      restore(note_id, commit_id) { return action('version_restore_note', { note_id, commit_id }); },
      release(name, message) { return action('version_create_release', { name, message }); },
      releases() { return action('version_list_releases', {}); },
      rollback(release_id) { return action('version_rollback_release', { release_id }); },
    },
    governance: {
      dashboard() { return action('governance_dashboard', {}); },
      issues(payload) { return action('governance_issue_list', payload || {}); },
      applyFix(issue_id, fix_mode, payload) { return action('governance_apply_fix', { issue_id, fix_mode: fix_mode || 'proposal', payload: payload || {} }); },
      proposal(id, status) { return action('governance_read_proposal', { proposal_id: id, status: status || '' }); },
      conflicts() { return action('governance_conflict_report', {}); },
      review(ids, decision, review_notes) { return action('governance_bulk_review', { proposal_ids: ids, decision, review_notes }); },
      apply(id, status) { return action('governance_apply_proposal', { proposal_id: id, status: status || 'accepted' }); },
      suggest(proposal_id, diagnostic_code) { return action('governance_suggest_fix', { proposal_id: proposal_id || '', diagnostic_code: diagnostic_code || '' }); },
      list(status) { return action('memory_list_proposals', { status: status || 'candidate' }); },
      decide(proposal_id, decision, review_notes) { return action('memory_review_proposal', { proposal_id, decision, review_notes: review_notes || '' }); },
    },
  };
  window.NoteGraph = window.NoteGraph || {};
  window.NoteGraph.api = api;
  window.GraphPedia = window.GraphPedia || {};
  window.GraphPedia.api = api;
  window.图谱百科 = window.图谱百科 || {};
  window.图谱百科.api = api;
})();
