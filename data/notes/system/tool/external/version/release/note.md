---
id: tool/external/version/release
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - version
---

# 创建发布快照

## Summary

创建发布快照。

## Fields

- 实体类型：工具
- 实体名称：创建发布快照
- 唯一标识：version.release
- executor_ref：builtin:version.release
- input_schema：{"type": "object", "properties": {"name": {"type": "string"}, "message": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：3
- categories：version
- activation_mode：manual
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：version

## Relations

- belongs_to: [[tool/external/version]]

## 工具说明

创建发布快照。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
