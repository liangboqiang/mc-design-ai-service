---
id: tool/external/shell/check
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - shell
---

# 命令安全检查

## Summary

检查命令是否符合离线安全策略。

## Fields

- 实体类型：工具
- 实体名称：命令安全检查
- 唯一标识：shell.check
- executor_ref：builtin:shell.check
- input_schema：{"type": "object", "properties": {"command": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：local_compute
- activation_mode：manual
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：shell

## Relations

- belongs_to: [[tool/external/shell]]

## 工具说明

检查命令是否符合离线安全策略。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
