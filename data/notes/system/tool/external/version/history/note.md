---
id: tool/external/version/history
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

# 查看版本历史

## Summary

查看全局或指定 note 的版本历史。

## Fields

- 实体类型：工具
- 实体名称：查看版本历史
- 唯一标识：version.history
- executor_ref：builtin:version.history
- input_schema：{"type": "object", "properties": {"note_id": {"type": "string"}, "limit": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：version
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：version

## Relations

- belongs_to: [[tool/external/version]]

## 工具说明

查看全局或指定 note 的版本历史。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
