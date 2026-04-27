(function () {
  const shell = window.MemoryNativeWorkbench = window.MemoryNativeWorkbench || {};
  shell.routes = shell.routes || {};
  shell.registerRoute = function registerRoute(name, render) {
    if (!name || typeof render !== 'function') return;
    shell.routes[name] = render;
  };
})();
