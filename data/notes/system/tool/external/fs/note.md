---
id: tool/external/fs
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

# 文件工具箱

## Summary

提供工作区内安全文件读写、差异、移动、删除和目录管理能力。

## Fields

- 实体类型：工具箱
- 唯一标识：fs
- 所属层级：基础工具层
- 激活方式：按智能体配置安装
- 安全边界：只暴露本工具箱声明的原子工具，不混入其他职责

## Relations

- contains: [[tool/external/fs/stat]]
- contains: [[tool/external/fs/list]]
- contains: [[tool/external/fs/read_text]]
- contains: [[tool/external/fs/write_text]]
- contains: [[tool/external/fs/replace_text]]
- contains: [[tool/external/fs/apply_patch]]
- contains: [[tool/external/fs/diff_text]]
- contains: [[tool/external/fs/mkdir]]
- contains: [[tool/external/fs/copy]]
- contains: [[tool/external/fs/move]]
- contains: [[tool/external/fs/delete]]

## 包含工具

- [[文件状态|tool/external/fs/stat]]
- [[列出文件|tool/external/fs/list]]
- [[读取文本|tool/external/fs/read_text]]
- [[写入文本|tool/external/fs/write_text]]
- [[替换文本|tool/external/fs/replace_text]]
- [[应用补丁|tool/external/fs/apply_patch]]
- [[文本差异|tool/external/fs/diff_text]]
- [[新建文件夹|tool/external/fs/mkdir]]
- [[复制文件|tool/external/fs/copy]]
- [[移动文件|tool/external/fs/move]]
- [[删除文件|tool/external/fs/delete]]
