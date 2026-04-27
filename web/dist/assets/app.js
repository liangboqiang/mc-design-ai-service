const api = (window.NoteGraph && window.NoteGraph.api) || (window.图谱百科 && window.图谱百科.api) || (window.GraphPedia && window.GraphPedia.api);
if (!api) { throw new Error('前端 API 未初始化：请确认 api.js 已在 app.js 之前加载。'); }

const 状态 = {
  查询: '',
  激活词条: { kind: [], domain: [], relation: [], status: [], repo: [], issue: [] },
  最近搜索: null,
  当前Note: '',
  当前仓库: 'team.default',
  当前模式: 'schema.part_design',
  当前问题: null,
  当前选中节点: null,
  图谱库状态: '离线图谱组件准备中',
  图谱布局: 'force',
  图谱实例: null,
  图谱实例表: {},
  当前图谱: null,
  当前笔记列表: [],
  当前激活邻居: [],
};

const 取 = (id) => document.getElementById(id);
const 转义 = (v) => String(v ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
const 截断 = (v, n = 96) => { const s = String(v ?? ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
const 编码 = encodeURIComponent;
const JSON文本 = (v) => 转义(JSON.stringify(v, null, 2));
const 唯一 = (arr) => [...new Set((arr || []).filter(Boolean))];
function 跳转(hash) { location.hash = hash; }
function 参数() { return new URLSearchParams((location.hash.split('?')[1] || '').trim()); }
function 页面名() {
  const h = location.hash || '#/';
  if (h.startsWith('#/note')) return '笔记详情';
  if (h.startsWith('#/repo')) return '记事本';
  if (h.startsWith('#/governance')) return '审核治理';
  return '图谱百科';
}
function 页面副标题() {
  const name = 页面名();
  if (name === '图谱百科') return '用一个页面完成检索、图谱索引、百科阅读和问题定位。';
  if (name === '记事本') return '以记事本组织系统内置笔记、团队资料和用户临时文件；每个笔记仍然进入 note.md 详情治理。';
  if (name === '审核治理') return '健康检查优先，集中处理冲突、缺证据、断链、待审核和修复建议。';
  return '以 note.md 为主体，治理版本、关系、证据和局部图谱。';
}
function 提示(text) {
  const node = document.createElement('div');
  node.className = '提示';
  node.textContent = text;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 2400);
}
function 空状态(text = '暂无数据') { return `<div class="空状态"><span>∅</span><p>${转义(text)}</p></div>`; }
function 加载(text = '正在加载...') { 渲染外壳(`<div class="加载"><span class="加载点"></span><p>${转义(text)}</p></div>`); }
function 指标(label, value, hint = '') { return `<div class="指标"><span>${转义(label)}</span><b>${转义(value)}</b>${hint ? `<small>${转义(hint)}</small>` : ''}</div>`; }
function 标签(text, cls = '') { return `<span class="标签 ${cls}">${转义(text || '未标注')}</span>`; }
function 按钮(label, onclick, cls = '次要') { return `<button class="按钮 ${cls}" onclick="${onclick}">${转义(label)}</button>`; }
function note链接(id) { return `#/note?id=${编码(id || '')}`; }
function 仓库相对路径(path, scope) {
  const p = String(path || '').replaceAll('\\', '/').replace(/^\/+/, '');
  if (scope === 'team' && p.startsWith('data/workbench/team/')) return p.slice('data/workbench/team/'.length);
  if (scope === 'user' && p.startsWith('data/workbench/user/')) return p.slice('data/workbench/user/'.length);
  return '';
}

function 渲染外壳(main, side = '', topExtra = '') {
  document.title = 页面名() + ' · NoteGraph';
  const h = location.hash || '#/';
  const nav = [
    ['#/', '图谱百科', '统一检索与图谱索引', '◈'],
    ['#/repo', '记事本', '系统笔记、源文件、软模式', '▦'],
    ['#/governance', '审核治理', '健康检查与修复', '◎'],
  ];
  取('root').innerHTML = `<div class="应用壳">
    <aside class="侧栏">
      <div class="品牌" onclick="跳转('#/')"><div class="品牌标记">N</div><div><strong>NoteGraph</strong><span>笔记图谱 · 原子动作</span></div></div>
      <nav>${nav.map(([href, label, desc, icon]) => `<a href="${href}" class="${(href === '#/' ? h === '#/' || h.startsWith('#/?') : h.startsWith(href)) ? '激活' : ''}"><i>${icon}</i><b>${label}</b><small>${desc}</small></a>`).join('')}</nav>
      <div class="侧栏说明"><b>四步闭环</b><span>图谱检索 → 笔记详情 → 仓库更新 → 健康治理</span></div>
    </aside>
    <main class="主区">
      <header class="顶栏"><div><div class="路径标识">NoteGraph 原子系统</div><h1>${转义(页面名())}</h1><p>${转义(页面副标题())}</p></div>${topExtra || ''}</header>
      <div class="内容网格 ${side ? '' : '单栏'}"><section class="主要内容">${main}</section>${side ? `<aside class="右栏">${side}</aside>` : ''}</div>
    </main>
  </div>`;
}

function 取节点类别(kind) {
  const k = String(kind || 'Note').toLowerCase();
  if (k.includes('agent')) return 'agent';
  if (k.includes('skill')) return 'skill';
  if (k.includes('tool')) return 'tool';
  if (k.includes('workflow')) return 'workflow';
  if (k.includes('part')) return 'part';
  if (k.includes('rule') || k.includes('policy')) return 'rule';
  if (k.includes('document') || k.includes('case') || k.includes('sop')) return 'document';
  return 'note';
}
function 图谱渲染状态() {
  if (window.NoteGraphForce && window.NoteGraphForce.mount) {
    状态.图谱库状态 = '离线高质量力导向图谱已启用';
    return true;
  }
  状态.图谱库状态 = '离线图谱组件未加载';
  return false;
}
function G6节点样式(kind, small = false) {
  const type = 取节点类别(kind);
  const table = {
    agent: ['#8b5cf6', '#ddd6fe', 50], skill: ['#06b6d4', '#cffafe', 42], tool: ['#f59e0b', '#fde68a', 46], workflow: ['#fb7185', '#ffe4e6', 44], part: ['#10b981', '#bbf7d0', 48], rule: ['#64748b', '#e2e8f0', 40], document: ['#38bdf8', '#dbeafe', 38], note: ['#3b82f6', '#bfdbfe', 36],
  };
  const [fill, stroke, size] = table[type] || table.note;
  return { size: small ? Math.max(20, size - 14) : size, style: { fill, stroke } };
}
function G6图谱数据(graph, limit = 220, small = false) {
  const sortedNodes = [...(graph.nodes || [])]
    .sort((a, b) => String(a.kind || '').localeCompare(String(b.kind || '')) || String(a.id).localeCompare(String(b.id)))
    .slice(0, limit);
  const nodeIds = new Set(sortedNodes.map((n) => n.id));
  const edgeSource = graph.visible_edges && graph.visible_edges.length ? graph.visible_edges : graph.edges || [];
  const edges = edgeSource.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target)).slice(0, limit * 2);
  return { ...graph, nodes: sortedNodes, edges, visible_edges: edges };
}
function 开源图谱加载失败(dom) {
  dom.innerHTML = `<div class="开源图谱失败"><b>离线图谱组件未加载</b><p>请确认 <code>assets/graphin_offline.js</code> 已包含在 <code>web/src/manifest.json</code> 中，并重新执行 <code>python scripts/build_web.py</code>。</p></div>`;
}
async function 挂载图谱(domId, graph, options = {}) {
  const dom = 取(domId);
  if (!dom) return;
  const ok = 图谱渲染状态();
  dom.innerHTML = '';
  if (!ok || !window.NoteGraphForce || !window.NoteGraphForce.mount) {
    开源图谱加载失败(dom);
    return;
  }
  if (状态.图谱实例表[domId]) { try { 状态.图谱实例表[domId].destroy(); } catch (e) { /* ignore */ } }
  const data = G6图谱数据(graph, options.limit || 220, !!options.small);
  const inst = window.NoteGraphForce.mount(dom, data, {
    ...options,
    onSelect: (id) => 激活图谱节点(id),
    onClear: () => 清空图谱激活(),
  });
  状态.图谱实例表[domId] = inst;
  if (domId === '主图谱') 状态.图谱实例 = inst;
  if (!options.small && 状态.当前选中节点) setTimeout(() => 应用图谱激活(状态.当前选中节点), 80);
}

function 笔记卡片(note, reason = '') {
  const id = note.note_id || note.id || note.page_id || '';
  return `<article class="知识卡片" onclick="跳转('${note链接(id)}')">
    <div class="卡片头"><strong>${转义(note.title || id)}</strong>${标签(note.kind || 'Note', '类型')}</div>
    <p>${转义(截断(note.summary || '暂无摘要', 150))}</p>
    <div class="卡片脚"><code>${转义(id)}</code><span>${转义(note.status || '')} / ${转义(note.maturity || '')}</span></div>
    ${reason ? `<small>${转义(reason)}</small>` : ''}
  </article>`;
}
function 下拉词条组(key, label, items) {
  const active = new Set(状态.激活词条[key] || []);
  const rows = items.map((item) => `<button class="词条选项 ${active.has(item) ? '选中' : ''}" onclick="切换词条('${key}', '${转义(item)}')"><span>${active.has(item) ? '✓' : '+'}</span>${转义(item)}</button>`).join('');
  const count = active.size ? ` ${active.size}` : '';
  return `<details class="词条下拉"><summary>${转义(label)}<em>${count}</em></summary><div class="词条面板">${rows}</div></details>`;
}
function 图谱查节点(id) {
  return (状态.当前图谱?.nodes || []).find((n) => n.id === id || n.note_id === id) || null;
}
function 图谱查笔记(id) {
  return (状态.当前笔记列表 || []).find((n) => (n.note_id || n.id || n.page_id) === id) || null;
}
function 图谱相关边(id) {
  const graph = 状态.当前图谱 || {};
  const edges = graph.visible_edges && graph.visible_edges.length ? graph.visible_edges : graph.edges || [];
  return edges.filter((e) => e.source === id || e.target === id);
}
function 图谱邻居节点(id) {
  const ids = new Set(图谱相关边(id).flatMap((e) => [e.source, e.target]).filter((x) => x && x !== id));
  return [...ids].map((nid) => 图谱查节点(nid)).filter(Boolean);
}
function 图谱图例(graph, notes) {
  const edges = graph.visible_edges && graph.visible_edges.length ? graph.visible_edges : graph.edges || [];
  const countKind = (kind) => edges.filter((e) => String(e.kind || '').toLowerCase() === kind).length;
  return `<div class="图谱图例">
    <div class="图例标题"><b>图谱画板</b><span>${转义(状态.图谱库状态)} · 力导向</span></div>
    <div class="图例统计"><span>节点 <b>${graph.nodes?.length || 0}</b></span><span>关系 <b>${edges.length}</b></span><span>笔记 <b>${notes.length}</b></span><span>问题 <b>${graph.diagnostics?.length || 0}</b></span></div>
    <div class="图例行"><i class="点 agent"></i>智能体 <i class="点 skill"></i>技能 <i class="点 tool"></i>工具 <i class="点 part"></i>零部件</div>
    <div class="图例行"><i class="线 declared"></i>声明 ${countKind('declared')} <i class="线 runtime"></i>运行 ${countKind('runtime')} <i class="线 inferred"></i>推断 ${countKind('inferred')} <i class="线 linked"></i>链接 ${countKind('linked')}</div>
    <div class="图例提示">单击节点只激活局部邻域；右侧卡片负责打开详情。</div>
  </div>`;
}
function 搜索选项栏(facets = {}) {
  const kinds = 唯一(['Agent', 'Skill', 'Tool', 'Workflow', 'Part', 'Parameter', 'Rule', 'SOP', 'Case', 'Document', ...(facets.kind || []).map((x) => x.value)]);
  return `<div class="选项栏">
    ${下拉词条组('kind', '对象类型', kinds)}
    ${下拉词条组('domain', '业务域', ['连杆', '曲轴', '凸轮轴', 'NX', '数据库', '参数化设计', '报告生成', '设计校核'])}
    ${下拉词条组('relation', '关系类型', ['uses', 'can_activate', 'depends_on', 'constrains', 'derived_from', 'produces', 'references', 'implements', 'configured_by'])}
    ${下拉词条组('status', '状态', ['published', 'draft', 'candidate', 'conflict', 'deprecated', 'runtime_ready', 'missing_evidence'])}
    ${下拉词条组('repo', '仓库', ['智能体仓库', '团队仓库', '用户临时仓库', '系统配置'])}
    ${下拉词条组('issue', '质量问题', ['缺 Evidence', '缺 Relations', '断链', '冲突', '重复 note_id', 'runtime_ready 失败', '软模式 推荐字段缺失'])}
  </div><div class="已激活选项">${Object.entries(状态.激活词条).flatMap(([k, arr]) => arr.map((v) => `<button onclick="切换词条('${k}', '${转义(v)}')">${转义(v)} ×</button>`)).join('') || '<span>选择下拉选项进行检索增强</span>'}</div>`;
}
function 渲染激活结果(id) {
  const box = 取('百科结果内容');
  const title = 取('右侧结果标题');
  const graph = 状态.当前图谱 || {};
  const node = 图谱查节点(id) || {};
  const note = 图谱查笔记(id) || { note_id: id, id, title: node.title || node.full || id, kind: node.kind || 'Note', status: node.status || '', maturity: node.maturity || '', summary: node.summary || '该节点来自图谱索引，点击下方按钮进入 note.md 详情。' };
  const edges = 图谱相关边(id);
  const neighbors = 图谱邻居节点(id).slice(0, 12).map((n) => ({ note_id: n.id, id: n.id, title: n.title || n.id, kind: n.kind || 'Note', status: n.status || '', maturity: n.maturity || '' }));
  if (title) title.innerHTML = `<h3>已激活笔记</h3><span>${转义(id)}</span>`;
  if (!box) return;
  box.innerHTML = `<article class="激活笔记卡">
    <div class="节点详情卡"><div class="节点徽标 ${取节点类别(note.kind)}">${转义(String(note.kind || 'N').slice(0, 1))}</div><div><h3>${转义(note.title || id)}</h3><code>${转义(id)}</code></div></div>
    <p>${转义(截断(note.summary || '暂无摘要', 180))}</p>
    <div class="标签行">${标签(note.kind || 'Note', '类型')}${标签(note.status || '', '状态')}${标签(note.maturity || '', '成熟度')}</div>
    <div class="操作组"><button class="按钮 主要" onclick="跳转('${note链接(id)}')">打开 note.md 详情</button><button class="按钮 次要" onclick="清空图谱激活()">清除激活</button></div>
  </article>
  <div class="区块标题 小标题"><h3>局部关系</h3><span>${edges.length} 条</span></div>
  ${edges.slice(0, 10).map((e) => `<div class="关系项"><b>${转义(e.source)}</b><span>${转义(e.predicate || e.kind || '关联')}</span><b>${转义(e.target)}</b></div>`).join('') || 空状态('暂无关系')}
  <div class="区块标题 小标题"><h3>邻近笔记</h3><span>${neighbors.length} 个</span></div>
  ${neighbors.map((n) => 笔记卡片(n)).join('') || 空状态('暂无邻居')}`;
}
function 应用图谱激活(id) {
  const g = 状态.图谱实例;
  if (g && g.selectNode) g.selectNode(id);
}
window.激活图谱节点 = (id) => {
  状态.当前选中节点 = id;
  应用图谱激活(id);
  渲染激活结果(id);
};
window.清空图谱激活 = () => {
  状态.当前选中节点 = null;
  const g = 状态.图谱实例;
  if (g && g.clear) g.clear();
  const title = 取('右侧结果标题');
  const box = 取('百科结果内容');
  if (title) title.innerHTML = `<h3>百科结果</h3><span>${(状态.当前笔记列表 || []).length} 条</span>`;
  if (box) box.innerHTML = (状态.当前笔记列表 || []).map((n) => 笔记卡片(n)).join('') || 空状态('没有匹配的笔记');
};
window.选择后备节点 = (id) => { 激活图谱节点(id); };

async function 渲染图谱百科() {
  const q = 参数().get('q');
  if (q !== null) 状态.查询 = q;
  加载('正在进行图谱式 + 百科式混合检索...');
  const filters = { ...状态.激活词条 };
  const data = await api.note.search({ query: 状态.查询, filters, include_hidden: true, limit: 140 });
  状态.最近搜索 = data;
  const notes = data.notes || [];
  const graph = data.graph || { nodes: [], edges: [], diagnostics: [] };
  状态.当前图谱 = graph;
  状态.当前笔记列表 = notes;
  const main = `<section class="检索头 图谱检索台">
    <div class="搜索框"><input id="统一搜索框" value="${转义(状态.查询)}" placeholder="检索 note、参数、工具、关系、文件与问题节点..."/><button class="按钮 主要" onclick="执行搜索()">检索图谱</button></div>
    <div class="搜索说明">搜索框、下拉选项和已激活选项共同组成一次图谱检索。</div>
    ${搜索选项栏(data.facets || {})}
  </section>
  <section class="图谱百科布局">
    <div class="图谱面板"><div class="图谱工具条"><div><b>离线力导向图谱</b><span id="图谱状态">${转义(状态.图谱库状态)}</span></div><div>${按钮('全量重建', '全量重建图谱()', '幽灵')}${按钮('重排力图', '重排图谱()', '幽灵')}${按钮('适配视图', '适配图谱()', '幽灵')}</div></div><div class="图谱画布包装"><div id="主图谱" class="开源图谱画布"></div>${图谱图例(graph, notes)}</div></div>
    <aside class="百科结果"><div class="区块标题" id="右侧结果标题"><h3>百科结果</h3><span>${notes.length} 条</span></div><div id="百科结果内容">${notes.map((n) => 笔记卡片(n)).join('') || 空状态('没有匹配的笔记')}</div><div class="右侧提示">图谱节点只负责激活局部范围；从这里点击卡片进入笔记详情。</div></aside>
  </section>
  <section class="图谱问题条"><b>问题摘要</b>${(graph.diagnostics || []).slice(0, 5).map((d) => `<span>${转义(d.code || '诊断')}：${转义(截断(d.message || d.note_id || '', 58))}</span>`).join('') || '<span>当前检索范围暂无明显问题</span>'}<button class="按钮 小" onclick="跳转('#/governance')">进入审核治理</button></section>`;
  渲染外壳(main);
  取('统一搜索框').onkeydown = (e) => { if (e.key === 'Enter') 执行搜索(); };
  await 挂载图谱('主图谱', graph, { limit: 220 });
  const status = 取('图谱状态'); if (status) status.textContent = 状态.图谱库状态;
  if (状态.当前选中节点) 渲染激活结果(状态.当前选中节点);
}

window.执行搜索 = () => {
  const input = 取('统一搜索框');
  if (input) 状态.查询 = input.value.trim();
  状态.当前选中节点 = null;
  location.hash = '#/?q=' + 编码(状态.查询.trim());
  渲染图谱百科();
};
window.全量重建图谱 = async () => { await api.graph.compile(true, true); 提示('图谱已全量重建'); 渲染图谱百科(); };
window.适配图谱 = () => { if (状态.图谱实例 && 状态.图谱实例.fitView) 状态.图谱实例.fitView(); };
window.重排图谱 = () => { if (状态.图谱实例 && 状态.图谱实例.relayout) 状态.图谱实例.relayout(); };

function 渲染Markdown(md) {
  const lines = String(md || '').split('\n');
  return lines.map((line) => {
    if (/^###\s+/.test(line)) return `<h3>${转义(line.replace(/^###\s+/, ''))}</h3>`;
    if (/^##\s+/.test(line)) return `<h2>${转义(line.replace(/^##\s+/, ''))}</h2>`;
    if (/^#\s+/.test(line)) return `<h1>${转义(line.replace(/^#\s+/, ''))}</h1>`;
    if (/^[-*]\s+/.test(line)) return `<p class="列表项">• ${转义(line.replace(/^[-*]\s+/, ''))}</p>`;
    if (!line.trim()) return '<br/>';
    const html = 转义(line).replace(/\[\[([^\]]+)\]\]/g, (_, id) => `<a class="note跳转" href="${note链接(id)}">${转义(id)}</a>`);
    return `<p>${html}</p>`;
  }).join('');
}
async function 渲染笔记详情() {
  const id = 参数().get('id') || 状态.当前Note;
  if (!id) { 跳转('#/'); return; }
  状态.当前笔记 = id;
  加载('正在读取 note.md 详情...');
  const [data, neighborData] = await Promise.all([api.note.read(id), api.graph.neighbors(id, 1).catch(() => ({ nodes: [], edges: [] }))]);
  const note = data.note || {};
  const markdown = data.markdown || '';
  const history = data.history || [];
  const diagnostics = data.diagnostics || [];
  const graph = data.neighbors || neighborData || { nodes: [], edges: [] };
  const front = `<div class="详情摘要"><div>${标签(note.kind, '类型')}${标签(note.status, '状态')}${标签(note.maturity, '成熟度')}</div><code>${转义(id)}</code></div>`;
  const main = `<section class="Note标题"><div><h2>${转义(note.title || id)}</h2>${front}</div><div class="操作组">${按钮('编辑源码', '切换编辑器()', '幽灵')}${按钮('保存', `保存Note源码('${转义(id)}', false)`, '次要')}${按钮('提交审核', `提交Note审核('${转义(id)}')`, '主要')}${按钮('发布', `发布笔记('${转义(id)}')`, '幽灵')}</div></section>
  <section class="Note详情布局"><aside class="Note目录"><a href="#摘要">摘要</a><a href="#字段">字段</a><a href="#关系">关系</a><a href="#证据">证据</a><a href="#历史">历史版本</a></aside><article class="Note正文"><div id="Note阅读区">${渲染Markdown(markdown)}</div><textarea id="Note源码" class="源码编辑 隐藏">${转义(markdown)}</textarea></article><aside class="Note治理"><h3>治理侧栏</h3>${指标('诊断问题', diagnostics.length)}${指标('历史版本', history.length)}${指标('邻居节点', graph.nodes?.length || 0)}<div id="小图谱" class="小图谱"></div><button class="按钮 次要 满宽" onclick="跳转('#/governance')">查看健康问题</button></aside></section>
  <section class="下方标签"><details open><summary>历史版本</summary>${history.slice(0, 8).map((h) => `<div class="行"><b>${转义(h.message || h.commit_id)}</b><span>${转义(h.created_at || '')}</span><button class="按钮 小" onclick="恢复笔记('${转义(id)}','${转义(h.commit_id)}')">回退</button></div>`).join('') || 空状态('暂无历史')}</details><details><summary>诊断与冲突</summary><pre>${JSON文本(diagnostics)}</pre></details><details><summary>原始详情</summary><pre>${JSON文本(note)}</pre></details></section>`;
  渲染外壳(main);
  await 挂载图谱('小图谱', graph, { limit: 26, small: true });
}
window.切换编辑器 = () => { 取('Note阅读区')?.classList.toggle('隐藏'); 取('Note源码')?.classList.toggle('隐藏'); };
window.保存Note源码 = async (id, commit) => { const md = 取('Note源码')?.value || ''; await api.note.save(id, md, commit, commit ? '人工保存并提交' : '人工保存草稿'); 提示(commit ? '已保存并提交版本' : '已保存 note.md'); };
window.提交Note审核 = async (id) => { const md = 取('Note源码')?.value || ''; await api.note.proposal(id, md, 'note_patch', '从详情页提交审核'); 提示('已创建待审核 Proposal'); };
window.发布笔记 = async (id) => { await api.note.publish(id, 'projectable'); 提示('已发布笔记'); 渲染笔记详情(); };
window.恢复笔记 = async (id, commit) => { if (!confirm('确认回退该笔记到选中版本？')) return; await api.version.restore(id, commit); 提示('已执行回退'); 渲染笔记详情(); };

// 记事本是唯一文件与配置入口；旧仓库表单已删除，避免双入口与兼容分叉。
window.增量索引当前仓库 = async () => { await api.graph.compile(true, true); 提示('已完成当前索引更新'); };
window.切换模式 = (id) => { 状态.当前模式 = id; 渲染模式摘要(); };
async function 渲染模式摘要() { const box = 取('模式摘要'); if (!box) return; const data = await api.schema.read(状态.当前模式).catch(() => ({ schema: {} })); const s = data.schema || {}; box.innerHTML = `<div class="小项"><b>${转义(s.name || s.schema_id)}</b><span>${转义(s.description || '')}</span></div><h4>推荐字段</h4>${(s.recommended_fields || []).slice(0, 12).map((f) => `<div class="字段项"><span>${转义(f.name)}</span><small>${转义(f.type || 'text')}</small></div>`).join('') || 空状态('暂无推荐字段')}<h4>候选字段</h4>${(s.candidate_fields || []).slice(0, 12).map((f) => `<div class="字段项"><span>${转义(f.name)}</span><button class="按钮 小" onclick="接受字段('${转义(f.name)}')">接受</button></div>`).join('') || 空状态('暂无候选字段')}`; }
window.发现模式字段 = async () => { await api.schema.discover(状态.当前模式, 状态.当前仓库); 提示('已自动增量发现字段'); 渲染模式摘要(); };
window.接受字段 = async (name) => { const type = prompt('字段类型', 'text') || 'text'; await api.schema.acceptField(状态.当前模式, name, { type }); 提示('字段已加入软模式'); 渲染模式摘要(); };


function 笔记本源定位(nb) {
  const src = String(nb.source_path || '').replaceAll('\\', '/');
  if (src.startsWith('data/workbench/user')) return { scope: 'user', base: src.slice('data/workbench/user'.length).replace(/^\/+/, '') };
  if (src.startsWith('data/workbench/team')) return { scope: 'team', base: src.slice('data/workbench/team'.length).replace(/^\/+/, '') };
  return { scope: 'team', base: src };
}
function 笔记本文件路径(nb, itemPath) {
  const loc = 笔记本源定位(nb);
  return [loc.base, itemPath || ''].filter(Boolean).join('/');
}
async function 渲染记事本() {
  加载('正在打开记事本...');
  const [nbData, schemaData] = await Promise.all([api.notebook.list().catch(() => ({ notebooks: [] })), api.schema.list().catch(() => ({ schemas: [] }))]);
  const notebooks = nbData.notebooks || [];
  if (!notebooks.find((x) => x.notebook_id === 状态.当前仓库) && notebooks[0]) 状态.当前仓库 = notebooks[0].notebook_id;
  const currentId = 状态.当前仓库 || (notebooks[0] && notebooks[0].notebook_id) || '';
  const detail = currentId ? await api.notebook.read(currentId).catch(() => ({ notebook: null })) : { notebook: null };
  const nb = detail.notebook || notebooks.find((x) => x.notebook_id === currentId) || {};
  const schemas = schemaData.schemas || [];
  const sourceLoc = 笔记本源定位(nb);
  const schemaOptions = schemas.map((s) => `<option value="${转义(s.schema_id)}" ${s.schema_id === (nb.soft_schema_id || 状态.当前模式) ? 'selected' : ''}>${转义(s.name || s.schema_id)}</option>`).join('');
  const cards = notebooks.map((x) => `<button class="仓库卡 ${x.notebook_id === currentId ? '选中' : ''}" onclick="选择笔记本('${转义(x.notebook_id)}')"><b>${转义(x.icon || '📒')} ${转义(x.name)}</b><span>${转义(x.notebook_type)} · ${转义(x.path)}</span><small>${转义(x.note_kind || '全部类型')} · ${x.note_count || 0} 条笔记 · 软模式：${转义(x.soft_schema_id || '无')}</small></button>`).join('');
  const noteRows = (nb.notes || nb.notes_preview || []).map((note) => `<article class="笔记摘要卡" onclick="跳转('${note链接(note.note_id)}')"><div><b>${转义(note.title || note.note_id)}</b><span>${转义(note.kind)} · ${转义(note.status)} / ${转义(note.maturity)}</span></div><p>${转义(截断(note.summary || '暂无摘要', 150))}</p><code>${转义(note.note_id)}</code></article>`).join('') || 空状态('这个记事本暂无 note.md。');
  const sourceFiles = (nb.source_files || []).slice(0, 80).map((f) => `<div class="文件行" onclick="打开笔记本源文件('${转义(nb.notebook_id)}','${转义(f.path)}')"><span>${f.kind === 'folder' ? '📁' : '📄'}</span><b>${转义(f.name)}</b><small>${转义(f.kind)} · ${转义(f.modified_at || '')}</small><button class="按钮 小" onclick="event.stopPropagation(); 从笔记本文件生成Note('${转义(nb.notebook_id)}','${转义(f.path)}')">生成笔记</button></div>`).join('') || 空状态('暂无源文件。可在记事本设置中上传文件或文件夹。');
  const main = `<section class="仓库布局 记事本布局"><aside class="仓库列表"><div class="区块标题"><h3>记事本</h3><button class="按钮 小" onclick="新建笔记本()">新增</button></div>${cards || 空状态('暂无记事本')}</aside><section class="仓库主体"><section class="记事本头"><div class="记事本封面"><span>${转义(nb.icon || '📒')}</span></div><div><h2>${转义(nb.name || '未选择记事本')}</h2><p>${转义(nb.summary || nb.description || '记事本用于组织 note.md、源文件、软模式和抽取规则。')}</p><div class="标签行">${标签(nb.notebook_type || 'team', '状态')}${标签(nb.note_kind || '全部类型', '类型')}${标签(`${nb.note_count || 0} 条笔记`, '成熟度')}</div></div></section><section class="仓库表单"><label>记事本名称<input id="笔记本名称" value="${转义(nb.name || '')}"/></label><label>笔记本路径<input id="笔记本路径" value="${转义(nb.path || '')}"/></label><label>笔记类型<input id="笔记类型" value="${转义(nb.note_kind || '')}" placeholder="Agent / Skill / Toolbox / Tool"/></label><label>类型<select id="笔记本类型"><option value="builtin" ${nb.notebook_type === 'builtin' ? 'selected' : ''}>系统内置</option><option value="team" ${nb.notebook_type === 'team' ? 'selected' : ''}>团队记事本</option><option value="user" ${nb.notebook_type === 'user' ? 'selected' : ''}>用户临时</option></select></label><label>源文件路径<input id="源文件路径" value="${转义(nb.source_path || '')}"/></label><label>软模式<select id="笔记本模式" ${nb.notebook_type === 'user' ? 'disabled' : ''}>${schemaOptions}</select></label><label>抽取规则<input id="笔记本规则" value="${转义(nb.extraction_rule_id || 'rule.default')}"/></label><label>图标<input id="笔记本图标" value="${转义(nb.icon || '📒')}"/></label><div class="操作组">${按钮('保存记事本', '保存当前笔记本()', '主要')}${按钮('自动发现字段', '发现当前笔记本字段()', '次要')}${按钮('增量索引', '增量索引当前仓库()', '次要')}${按钮('全量重建', '全量重建图谱()', '幽灵')}</div></section><section class="记事本双栏"><div><div class="区块标题"><h3>笔记摘要</h3><span>点击卡片进入 note.md 详情页</span></div><div class="笔记摘要列表">${noteRows}</div></div><div><div class="区块标题"><h3>源文件</h3><div>${按钮('新建文件夹', '新建笔记本文件夹()', '幽灵')}${按钮('上传源文件 / 文件夹', '触发笔记本上传()', '主要')}</div></div><input id="笔记本源上传" type="file" multiple webkitdirectory class="隐藏"/><div class="文件列表">${sourceFiles}</div></div></section></section></section>`;
  const side = `<section class="侧卡"><h3>详情摘要</h3><p>记事本只是组织入口；每个笔记仍然以 note.md 详情页为主，可在详情页完成编辑、审核、版本回溯和小型图谱跳转。</p>${指标('笔记数', nb.note_count || 0)}${指标('源文件', (nb.source_files || []).length)}${指标('软模式', nb.soft_schema_id || '无')}</section><section class="侧卡"><h3>当前软模式</h3><button class="按钮 次要 满宽" onclick="发现当前笔记本字段()">从当前记事本增量发现字段</button><div id="模式摘要"></div></section>`;
  状态.当前模式 = nb.soft_schema_id || 状态.当前模式;
  渲染外壳(main, side);
  const upload = 取('笔记本源上传');
  if (upload) upload.onchange = 上传笔记本源文件;
  await 渲染模式摘要();
}
window.选择笔记本 = (id) => { 状态.当前仓库 = id; 渲染记事本(); };
window.新建笔记本 = async () => { const id = prompt('请输入记事本 ID，例如 notebook.connecting_rod'); if (!id) return; await api.notebook.save({ notebook_id: id, name: id, notebook_type: 'team', path: `data/notes/custom/${id.replaceAll('.', '_')}`, note_kind: 'Document', soft_schema_id: 'schema.business_document', extraction_rule_id: 'rule.default', source_path: `data/workbench/team/notebooks/${id.replaceAll('.', '_')}/sources`, icon: '📒' }); 状态.当前仓库 = id; 渲染记事本(); };
window.保存当前笔记本 = async () => { const nb = { notebook_id: 状态.当前仓库, name: 取('笔记本名称').value, path: 取('笔记本路径').value, note_kind: 取('笔记类型').value, notebook_type: 取('笔记本类型').value, source_path: 取('源文件路径').value, soft_schema_id: 取('笔记本模式')?.value || '', extraction_rule_id: 取('笔记本规则').value, icon: 取('笔记本图标').value || '📒' }; await api.notebook.save(nb); 提示('记事本已保存'); 渲染记事本(); };
window.触发笔记本上传 = () => 取('笔记本源上传').click();
async function 上传笔记本源文件(e) { const files = [...(e.target.files || [])]; if (!files.length) return; const data = await api.notebook.read(状态.当前仓库); const nb = data.notebook || {}; const loc = 笔记本源定位(nb); const rows = await Promise.all(files.map(async (file) => ({ name: file.name, relative_path: file.webkitRelativePath || file.name, content: await file.text() }))); await api.workspace.upload(loc.scope, loc.base, rows); 提示(`已上传 ${rows.length} 个源文件`); 渲染记事本(); }
window.新建笔记本文件夹 = async () => { const name = prompt('新建源文件夹名称'); if (!name) return; const data = await api.notebook.read(状态.当前仓库); const nb = data.notebook || {}; const loc = 笔记本源定位(nb); await api.workspace.mkdir(loc.scope, [loc.base, name].filter(Boolean).join('/')); 渲染记事本(); };
window.打开笔记本源文件 = async (notebookId, itemPath) => { const data = await api.notebook.read(notebookId); const nb = data.notebook || {}; const loc = 笔记本源定位(nb); const full = 笔记本文件路径(nb, itemPath); const payload = await api.workspace.read(loc.scope, full); const content = prompt(`编辑源文件：${itemPath}`, payload.content || ''); if (content !== null) { await api.workspace.write(loc.scope, full, content); 提示('源文件已保存'); 渲染记事本(); } };
window.从笔记本文件生成Note = async (notebookId, itemPath) => { const data = await api.notebook.read(notebookId); const nb = data.notebook || {}; const loc = 笔记本源定位(nb); const full = 笔记本文件路径(nb, itemPath); await api.note.fromFile(loc.scope, full, nb.note_kind || 'Document', 'proposal'); 提示('已从源文件生成 note 候选'); };
window.发现当前笔记本字段 = async () => { const data = await api.notebook.read(状态.当前仓库); const nb = data.notebook || {}; const schema = nb.soft_schema_id || 状态.当前模式; if (!schema) return 提示('用户临时记事本不绑定软模式'); 状态.当前模式 = schema; await api.schema.discover(schema, 状态.当前仓库); 提示('已从当前记事本增量发现字段'); 渲染模式摘要(); };

async function 渲染审核治理() {
  加载('正在执行健康检查...');
  const [dashboard, issues] = await Promise.all([api.governance.dashboard().catch(() => ({})), api.governance.issues().catch(() => ({ issues: [] }))]);
  const rows = issues.issues || [];
  const main = `<section class="治理总览"><div class="指标网格">${指标('待审核', dashboard.proposals?.candidate || 0)}${指标('冲突项', dashboard.conflicts?.count || 0)}${指标('诊断问题', dashboard.graph?.diagnostics || rows.length)}${指标('图谱节点', dashboard.graph?.nodes || 0)}</div></section><section class="治理布局"><aside class="问题列表">${rows.map((x) => `<button class="问题卡 ${x.severity}" onclick="查看问题('${转义(x.issue_id)}')"><b>${转义(x.title)}</b><span>${转义(截断(x.summary, 120))}</span><small>${转义(x.code)} · ${转义(x.risk_level)}</small></button>`).join('') || 空状态('暂无健康问题')}</aside><section class="问题详情" id="问题详情"><h3>问题摘要</h3><p>选择左侧问题节点查看摘要、Diff、影响分析和修复建议。</p></section></section>`;
  const side = `<section class="侧卡"><h3>批量治理</h3><p>低风险项可按建议批量处理；涉及 note_id、执行器、删除、回退的高风险项必须逐项确认。</p><button class="按钮 主要 满宽" onclick="批量接受候选()">批量接受候选</button><button class="按钮 次要 满宽" onclick="全量重建图谱()">重新健康检查</button></section><section class="侧卡"><h3>版本状态</h3><pre>${JSON文本(dashboard.version || {})}</pre></section>`;
  渲染外壳(main, side);
  window.__当前问题 = rows;
}
window.查看问题 = async (issueId) => { const issue = (window.__当前问题 || []).find((x) => x.issue_id === issueId) || {}; const box = 取('问题详情'); if (!box) return; let proposalDetail = ''; if (issue.kind === 'proposal' && issue.issue_id?.startsWith('proposal:')) { const pid = issue.issue_id.split(':')[1]; try { const data = await api.governance.proposal(pid); proposalDetail = `<h4>Diff 预览</h4><pre>${JSON文本(data.diff || {})}</pre><h4>影响分析</h4><pre>${JSON文本(data.impact || {})}</pre>`; } catch (e) { proposalDetail = `<p>${转义(e.message)}</p>`; } } box.innerHTML = `<h3>${转义(issue.title || '健康问题')}</h3><p>${转义(issue.summary || '')}</p><div class="标签行">${标签(issue.severity, '状态')}${标签(issue.risk_level, '成熟度')}${标签(issue.kind, '类型')}</div><h4>修复建议</h4><p>${转义(issue.suggestion || '查看详情后生成修复 Proposal。')}</p><div class="操作组"><button class="按钮 主要" onclick="智能修复('${转义(issue.issue_id)}')">按建议智能处理</button>${issue.note_id ? `<button class="按钮 次要" onclick="跳转('${note链接(issue.note_id)}')">打开笔记</button>` : ''}</div>${proposalDetail}<h4>原始问题</h4><pre>${JSON文本(issue.details || issue)}</pre>`; };
window.智能修复 = async (issueId) => { const mode = confirm('是否直接接受/应用可处理候选？取消则仅生成修复建议。') ? 'accept' : 'proposal'; const res = await api.governance.applyFix(issueId, mode); 提示(res.status === 'accepted' ? '已按建议接受候选' : '已生成修复建议'); 渲染审核治理(); };
window.批量接受候选 = async () => { const rows = (window.__当前问题 || []).filter((x) => x.kind === 'proposal' && x.issue_id.startsWith('proposal:')).map((x) => x.issue_id.split(':')[1]); if (!rows.length) return 提示('没有可批量接受的候选'); await api.governance.review(rows, 'accepted', '低风险批量接受'); 提示(`已接受 ${rows.length} 个候选`); 渲染审核治理(); };

async function renderCurrent() {
  try {
    const h = location.hash || '#/';
    if (h.startsWith('#/note')) return 渲染笔记详情();
    if (h.startsWith('#/repo')) return 渲染记事本();
    if (h.startsWith('#/governance')) return 渲染审核治理();
    return 渲染图谱百科();
  } catch (err) {
    console.error(err);
    渲染外壳(`<div class="错误"><h2>页面错误</h2><p>${转义(err.message || err)}</p><button class="按钮 主要" onclick="renderCurrent()">重试</button></div>`);
  }
}
window.renderCurrent = renderCurrent;
window.addEventListener('hashchange', renderCurrent);
renderCurrent();

// AntV G6 / @antv/g6 兼容说明：当前离线沙盒无法拉取官方包，本地使用离线高质量力导向图谱组件；生产环境可替换为官方 Graphin/G6 bundle。
