---
id: tool/external/shell
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

# 本地检查工具箱

## Summary

提供受限离线命令检查和运行能力，只用于构建、测试、静态检查和只读状态。

## Fields

- 实体类型：工具箱
- 唯一标识：shell
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/shell/check]]
- contains: [[tool/external/shell/run]]

## 包含工具

- [[命令安全检查|tool/external/shell/check]]
- [[运行本地命令|tool/external/shell/run]]
