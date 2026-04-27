---
id: tool/external/fs/replace_text
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - fs
---

# 替换文本

## Summary

在单个文件中替换明确匹配的文本片段。

## Fields

- 实体类型：工具
- 实体名称：替换文本
- 唯一标识：fs.replace_text
- executor_ref：builtin:files.replace_text
- input_schema：{"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：2
- categories：workspace_io
- activation_mode：skill
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：fs

## Relations

- belongs_to: [[tool/external/fs]]

## 工具说明

在单个文件中替换明确匹配的文本片段。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
