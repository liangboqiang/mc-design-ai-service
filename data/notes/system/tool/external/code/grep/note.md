---
id: tool/external/code/grep
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

# 代码内容检索

## Summary

在代码库中进行正则文本检索。

## Fields

- 实体类型：工具
- 实体名称：代码内容检索
- 唯一标识：code.grep
- executor_ref：builtin:code.grep
- input_schema：{"type": "object", "properties": {"pattern": {"type": "string"}, "file_glob": {"type": "string"}, "limit": {"type": "integer"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：code_search
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：code

## Relations

- belongs_to: [[tool/external/code]]

## 工具说明

在代码库中进行正则文本检索。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
