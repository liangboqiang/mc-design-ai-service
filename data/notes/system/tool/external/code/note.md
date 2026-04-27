---
id: tool/external/code
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

# 代码检索工具箱

## Summary

提供离线代码库文件发现、正则检索、窗口读取、符号提取和仓库地图能力。

## Fields

- 实体类型：工具箱
- 唯一标识：code
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/code/glob]]
- contains: [[tool/external/code/grep]]
- contains: [[tool/external/code/read_window]]
- contains: [[tool/external/code/symbols]]
- contains: [[tool/external/code/repo_map]]

## 包含工具

- [[代码文件匹配|tool/external/code/glob]]
- [[代码内容检索|tool/external/code/grep]]
- [[代码窗口读取|tool/external/code/read_window]]
- [[代码符号提取|tool/external/code/symbols]]
- [[仓库地图|tool/external/code/repo_map]]
