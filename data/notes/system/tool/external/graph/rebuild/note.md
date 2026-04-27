---
id: tool/external/graph/rebuild
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

# 重建图谱索引

## Summary

全量重建 note 索引和图谱索引。

## Fields

- 实体类型：工具
- 实体名称：重建图谱索引
- 唯一标识：graph.rebuild
- executor_ref：builtin:graph.rebuild
- input_schema：{"type": "object", "properties": {}}
- output_schema：{"type":"string"}
- permission_level：3
- categories：governance
- activation_mode：manual
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：graph

## Relations

- belongs_to: [[tool/external/graph]]

## 工具说明

全量重建 note 索引和图谱索引。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
