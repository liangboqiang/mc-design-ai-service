# Cytoscape.js vendor slot

Wiki Workbench V2 的图谱层通过 `GraphAdapter` 接口接入图谱渲染器。

- 如果后续需要使用完整 Cytoscape.js，可将官方 `cytoscape.min.js` 放入本目录，并在 `web/src/index.html` 中加载。
- 当前包保留离线可用的 SVG fallback，保证无外部依赖时图谱页仍可闭环显示。
- 前端接口已经按 Cytoscape 的 node/edge 数据结构组织，切换到完整 Cytoscape.js 不需要改后端 Action。
