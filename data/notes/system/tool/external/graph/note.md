---
id: tool/external/graph
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

# 图谱索引工具箱

## Summary

提供图谱式检索、邻域读取、索引重建和健康检查能力。

## Fields

- 实体类型：工具箱
- 唯一标识：graph
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/graph/search]]
- contains: [[tool/external/graph/neighbors]]
- contains: [[tool/external/graph/rebuild]]
- contains: [[tool/external/graph/health]]

## 包含工具

- [[图谱百科检索|tool/external/graph/search]]
- [[读取图谱邻域|tool/external/graph/neighbors]]
- [[重建图谱索引|tool/external/graph/rebuild]]
- [[图谱健康检查|tool/external/graph/health]]
