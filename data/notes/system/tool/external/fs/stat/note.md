---
id: tool/external/fs/stat
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

# 文件状态

## Summary

读取工作区文件或目录的存在性、类型、大小和修改时间。

## Fields

- 实体类型：工具
- 实体名称：文件状态
- 唯一标识：fs.stat
- executor_ref：builtin:files.stat
- input_schema：{"type": "object", "properties": {"path": {"type": "string"}}}
- output_schema：{"type":"string"}
- permission_level：1
- categories：workspace_io
- activation_mode：always
- safety：内网离线工具，只允许在授权工作区和权限等级内执行。
- 所属工具箱：fs

## Relations

- belongs_to: [[tool/external/fs]]

## 工具说明

读取工作区文件或目录的存在性、类型、大小和修改时间。

## 使用边界

- 只能通过 CapabilityDispatcher 调用。
- 不能绕过权限等级、路径边界和审核发布规则。
- 工具返回结果只作为执行观察或候选证据，不直接成为发布知识。

## Evidence

- evidence.system.tool_upgrade
