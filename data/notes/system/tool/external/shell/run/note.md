---
id: tool/external/shell/run
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

# 运行本地命令

## Summary

运行受限离线命令。默认不激活，需高权限。

## Fields

- 实体类型：工具
- 实体名称：运行本地命令
- 唯一标识：shell.run
- executor_ref：builtin:shell.run
- input_schema：{"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：4
- categories：local_compute
- activation_mode：manual
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：shell

## Relations

- belongs_to: [[tool/external/shell]]

## 工具说明

运行受限离线命令。默认不激活，需高权限。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
