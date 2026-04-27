---
id: tool/external/version
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

# 版本治理工具箱

## Summary

提供 note.md 的 Git-like 状态、提交、历史、差异、恢复、发布和回退能力。

## Fields

- 实体类型：工具箱
- 唯一标识：version
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/version/status]]
- contains: [[tool/external/version/commit]]
- contains: [[tool/external/version/history]]
- contains: [[tool/external/version/diff]]
- contains: [[tool/external/version/restore]]
- contains: [[tool/external/version/release]]
- contains: [[tool/external/version/rollback]]

## 包含工具

- [[版本状态|tool/external/version/status]]
- [[提交笔记版本|tool/external/version/commit]]
- [[查看版本历史|tool/external/version/history]]
- [[版本差异|tool/external/version/diff]]
- [[恢复笔记版本|tool/external/version/restore]]
- [[创建发布快照|tool/external/version/release]]
- [[回退发布|tool/external/version/rollback]]
