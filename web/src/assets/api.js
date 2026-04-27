(function () {
  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      const message = data && data.error && data.error.message ? data.error.message : ('Request failed: ' + response.status);
      throw new Error(message);
    }
    return data.data;
  }

  window.MemoryNativeWorkbench = window.MemoryNativeWorkbench || {};
  window.MemoryNativeWorkbench.api = {
    postJson,
    memory(action, payload) {
      return postJson('/app/memory/action/' + action, payload);
    },
    workbench(action, payload) {
      return postJson('/app/workbench/action/' + action, payload);
    },
    wiki(action, payload) {
      return postJson('/app/wiki/action/' + action, payload);
    },
  };
})();
