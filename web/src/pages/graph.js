const GraphAdapter = {
  render(container, graph, options = {}) {
    if (window.cytoscape) return this.renderCytoscape(container, graph, options);
    return this.renderSvg(container, graph, options);
  },
  renderCytoscape(container, graph, options = {}) {
    container.innerHTML = "";
    const elements = [...graph.nodes.map((n) => ({ data: { id: n.id, label: n.label, type: n.type, page_id: n.page_id } })), ...graph.edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.label } }))];
    const cy = window.cytoscape({ container, elements, layout: { name: "cose", animate: false } });
    cy.on("tap", "node", (evt) => options.onNodeClick?.(evt.target.data()));
    return cy;
  },
  renderSvg(container, graph, options = {}) {
    const width = Math.max(720, container.clientWidth || 720), height = Math.max(460, container.clientHeight || 460);
    const nodes = (graph.nodes || []).slice(0, 140), ids = new Set(nodes.map((n) => n.id));
    const edges = (graph.edges || []).filter((e) => ids.has(e.source) && ids.has(e.target)).slice(0, 240);
    const cx = width / 2, cy = height / 2, r = Math.min(width, height) * 0.38, pos = new Map();
    nodes.forEach((n, i) => { const a = Math.PI * 2 * i / Math.max(1, nodes.length); pos.set(n.id, { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r }); });
    const color = (type) => ({ tool: "#7c3aed", skill: "#16a34a", agent: "#ea580c", schema: "#64748b", page: "#2563eb", entity: "#0891b2", document: "#0f766e" }[String(type).toLowerCase()] || "#2563eb");
    container.innerHTML = `<svg class="graph-svg" viewBox="0 0 ${width} ${height}"><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"></path></marker></defs><g>${edges.map((e) => { const s = pos.get(e.source), t = pos.get(e.target); return s && t ? `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" marker-end="url(#arrow)"></line>` : ""; }).join("")}</g><g>${nodes.map((n) => { const p = pos.get(n.id); return `<g class="graph-node" data-id="${escapeHtml(n.id)}" transform="translate(${p.x},${p.y})"><circle r="15" fill="${color(n.type)}"></circle><text y="32">${escapeHtml(n.label).slice(0, 16)}</text></g>`; }).join("")}</g></svg>`;
    container.querySelectorAll("[data-id]").forEach((el) => {
      el.onclick = () => options.onNodeClick?.(nodes.find((n) => n.id === el.dataset.id));
      el.ondblclick = () => { const n = nodes.find((x) => x.id === el.dataset.id); if (n) route(pageLink(n.page_id || n.id)); };
    });
  }
};

function normalizeGraphData(data) {
  const graph = data?.graph || data || {};
  let nodes = graph.nodes || data.nodes || [];
  let edges = graph.edges || graph.links || data.edges || [];
  const triples = graph.triples || data.triples || [];
  nodes = nodes.map((n) => ({ id: String(n.id || n.page_id || n.label || n.name), label: String(n.label || n.title || n.name || n.id || n.page_id), type: String(n.type || n.kind || n.entity_type || "page"), page_id: String(n.page_id || n.id || ""), summary: String(n.summary || n.description || "") })).filter((n) => n.id);
  edges = edges.map((e, i) => ({ id: String(e.id || `edge-${i}`), source: String(e.source || e.from || ""), target: String(e.target || e.to || ""), label: String(e.label || e.predicate || e.relation || e.type || ""), kind: String(e.kind || ""), status: String(e.status || "") })).filter((e) => e.source && e.target);
  return { nodes, edges, triples, diagnostics: graph.diagnostics || data.diagnostics || [] };
}

async function drawLocalGraph(pageId) {
  try { GraphAdapter.render($("localGraph"), normalizeGraphData(await callMemoryAction("memory_graph_neighbors", { note_id: pageId, depth: 1 })), { onNodeClick: (node) => { if (node?.page_id || node?.id) route(pageLink(node.page_id || node.id)); } }); }
  catch { $("localGraph").innerHTML = `<div class="empty-state compact">局部图谱暂无数据</div>`; }
}

async function renderGraphImpl() {
  renderFrame(loadingView("正在读取图谱..."), "", { title: "Graph" });
  try {
    const graph = normalizeGraphData(await callMemoryAction("memory_graph_view", { include_hidden: false }));
    const diagnostics = graph.diagnostics || [];
    const main = `<section class="graph-toolbar"><input id="graphQuery" placeholder="过滤节点或关系..." /><select id="graphType"><option value="">全部类型</option><option value="tool">Tool</option><option value="skill">Skill</option><option value="agent">Agent</option><option value="document">Document</option></select><button id="graphFilterBtn" class="button primary">筛选</button></section><div class="graph-page"><section id="graphCanvas" class="graph-canvas"></section><aside id="graphDetail" class="context-pane embedded"><h3>Memory Graph</h3><p>默认展示 published declared/runtime 与 reviewed inferred。</p></aside></div><section class="panel"><h3>Graph Diagnostics</h3><pre>${escapeHtml(JSON.stringify(diagnostics.slice(0, 30), null, 2))}</pre></section>`;
    renderFrame(main, "", { title: "Graph", subtitle: `节点 ${graph.nodes.length} 个，关系 ${graph.edges.length} 条` });
    const draw = (g) => GraphAdapter.render($("graphCanvas"), g, { onNodeClick: (node) => { $("graphDetail").innerHTML = `<h3>${escapeHtml(node.label || node.id)}</h3><p>${escapeHtml(node.summary || "暂无摘要")}</p><code>${escapeHtml(node.page_id || node.id)}</code><button class="button primary full" onclick="route('${pageLink(node.page_id || node.id)}')">打开页面</button>`; } });
    draw(graph);
    $("graphFilterBtn").onclick = () => {
      const q = $("graphQuery").value.trim().toLowerCase();
      const type = $("graphType").value;
      const nodes = graph.nodes.filter((n) => (!q || `${n.label} ${n.id} ${n.summary}`.toLowerCase().includes(q)) && (!type || String(n.type).toLowerCase() === type));
      const ids = new Set(nodes.map((n) => n.id));
      draw({ ...graph, nodes, edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)) });
    };
  } catch (error) {
    setNotice("", String(error.message || error));
    renderFrame(`${notice()}${emptyView("图谱读取失败。")}`, "", { title: "Graph" });
  }
}

window.WikiWorkbenchPages.renderGraph = renderGraphImpl;
