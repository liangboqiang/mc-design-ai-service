---
id: tool/external/graph/search
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - graph
---

# 图谱百科检索

## Summary

基于 note.md 和图谱索引进行混合检索。

## Fields

- 实体类型：工具
- 实体名称：图谱百科检索
- 唯一标识：graph.search
- executor_ref：builtin:graph.search
- input_schema：{"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：memory_read
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：graph

## Relations

- belongs_to: [[tool/external/graph]]

## 工具说明

基于 note.md 和图谱索引进行混合检索。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
