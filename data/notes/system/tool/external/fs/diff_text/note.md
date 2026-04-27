---
id: tool/external/fs/diff_text
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

# 文本差异

## Summary

生成两个文本文件的 unified diff。

## Fields

- 实体类型：工具
- 实体名称：文本差异
- 唯一标识：fs.diff_text
- executor_ref：builtin:files.diff_text
- input_schema：{"type": "object", "properties": {"old_path": {"type": "string"}, "new_path": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：workspace_io
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：fs

## Relations

- belongs_to: [[tool/external/fs]]

## 工具说明

生成两个文本文件的 unified diff。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
