---
id: tool
kind: Document
status: published
maturity: projectable
lens: lens.default
source_refs:
  - evidence.system.tool_upgrade
tags:
  - 工具体系
---

# 系统工具体系

## Summary

本系统工具箱采用稳定原子能力集合：文件、代码、文档、笔记、图谱、版本、本地检查，以及垂类 NX 和报告工具。工具必须通过 CapabilitySpec 暴露，不允许绕过权限直接执行。

## Fields

- 体系名称：Memory-Native 基础工具体系
- 设计原则：覆盖场景全、职责清晰、相互不冲突、内网离线可运行
- 权限模型：只读、草稿、治理、系统

## Relations

- contains: [[tool/external/fs]]
- contains: [[tool/external/code]]
- contains: [[tool/external/docs]]
- contains: [[tool/external/notes]]
- contains: [[tool/external/graph]]
- contains: [[tool/external/version]]
- contains: [[tool/external/shell]]
- contains: [[tool/external/nx]]
- contains: [[tool/external/design_report]]
