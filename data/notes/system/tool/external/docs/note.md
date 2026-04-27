---
id: tool/external/docs
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

# 文档读取工具箱

## Summary

提供离线文档文本抽取、元数据读取和表格预览能力。

## Fields

- 实体类型：工具箱
- 唯一标识：docs
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/docs/extract_text]]
- contains: [[tool/external/docs/metadata]]
- contains: [[tool/external/docs/table_preview]]

## 包含工具

- [[抽取文档文本|tool/external/docs/extract_text]]
- [[读取文档元数据|tool/external/docs/metadata]]
- [[表格预览|tool/external/docs/table_preview]]
