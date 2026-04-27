---
id: tool/external/code/read_window
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - code
---

# 代码窗口读取

## Summary

按行号读取代码片段，适合大文件查看。

## Fields

- 实体类型：工具
- 实体名称：代码窗口读取
- 唯一标识：code.read_window
- executor_ref：builtin:code.read_window
- input_schema：{"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "window": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：code_read
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：code

## Relations

- belongs_to: [[tool/external/code]]

## 工具说明

按行号读取代码片段，适合大文件查看。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
