---
id: tool/external/docs/metadata
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

# 读取文档元数据

## Summary

读取文件后缀、大小和修改时间。

## Fields

- 实体类型：工具
- 实体名称：读取文档元数据
- 唯一标识：docs.metadata
- executor_ref：builtin:docs.metadata
- input_schema：{"type": "object", "properties": {"path": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：document
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：docs

## Relations

- belongs_to: [[tool/external/docs]]

## 工具说明

读取文件后缀、大小和修改时间。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
