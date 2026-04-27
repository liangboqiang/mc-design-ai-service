---
id: tool/external/version/status
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

# 版本状态

## Summary

查看 note.md 工作树状态和变更文件。

## Fields

- 实体类型：工具
- 实体名称：版本状态
- 唯一标识：version.status
- executor_ref：builtin:version.status
- input_schema：{"type": "object", "properties": {}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：version
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：version

## Relations

- belongs_to: [[tool/external/version]]

## 工具说明

查看 note.md 工作树状态和变更文件。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
