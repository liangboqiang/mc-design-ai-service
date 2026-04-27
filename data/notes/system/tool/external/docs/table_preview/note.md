---
id: tool/external/docs/table_preview
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - docs
---

# 表格预览

## Summary

预览 CSV/XLSX 表格前若干行。

## Fields

- 实体类型：工具
- 实体名称：表格预览
- 唯一标识：docs.table_preview
- executor_ref：builtin:docs.table_preview
- input_schema：{"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：document
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：docs

## Relations

- belongs_to: [[tool/external/docs]]

## 工具说明

预览 CSV/XLSX 表格前若干行。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
