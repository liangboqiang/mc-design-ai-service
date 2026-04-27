---
id: tool/external/notes/create
kind: Tool
status: published
maturity: runtime_ready
lens: lens.tool
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具
  - notes
---

# 新建笔记

## Summary

创建草稿状态 note.md。

## Fields

- 实体类型：工具
- 实体名称：新建笔记
- 唯一标识：notes.create
- executor_ref：builtin:notes.create
- input_schema：{"type": "object", "properties": {"note_id": {"type": "string"}, "kind": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：2
- categories：memory_write
- activation_mode：skill
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：notes

## Relations

- belongs_to: [[tool/external/notes]]

## 工具说明

创建草稿状态 note.md。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
