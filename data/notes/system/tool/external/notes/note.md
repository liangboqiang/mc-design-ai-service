---
id: tool/external/notes
kind: Toolbox
status: published
maturity: runtime_ready
lens: lens.default
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具箱
  - 内网
---

# 笔记工具箱

## Summary

提供 note.md 的检索、读取、检查、创建和受控更新能力。

## Fields

- 实体类型：工具箱
- 唯一标识：notes
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/notes/list]]
- contains: [[tool/external/notes/read]]
- contains: [[tool/external/notes/check]]
- contains: [[tool/external/notes/create]]
- contains: [[tool/external/notes/update_source]]
- contains: [[tool/external/notes/generate_from_text]]

## 包含工具

- [[列出笔记|tool/external/notes/list]]
- [[读取笔记|tool/external/notes/read]]
- [[检查笔记|tool/external/notes/check]]
- [[新建笔记|tool/external/notes/create]]
- [[更新笔记源码|tool/external/notes/update_source]]
- [[文本生成笔记|tool/external/notes/generate_from_text]]
