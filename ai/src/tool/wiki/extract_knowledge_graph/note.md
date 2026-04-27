---
id: tool/wiki/extract_knowledge_graph
kind: Tool
status: published
maturity: projectable
lens: lens.tool
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 工具：抽取知识图谱

摘要：根据全部 wiki.md 和元结构抽取三元组，禁用页面默认不参与图谱生成。

## 基本信息

- 实体类型：工具
- 实体名称：抽取知识图谱
- 唯一标识：wiki_app.extract_knowledge_graph
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25
- 所属工具箱：Wiki 治理工具箱
- 所属分类：Wiki、治理
- 权限等级：治理
- 激活方式：默认激活

## 元词条

- 关键词：抽取知识图谱、Wiki Agent、页面治理、知识图谱
- 别名：抽取知识图谱、wiki_app.extract_knowledge_graph
- 风险等级：中
- 作用范围：Wiki 页面、依赖文件、局部关系和图谱治理
- 局部关系：属于 [[Wiki 治理工具箱|tool/wiki]]
- 依赖文件：同目录相关文件
- 更新策略：差异化更新

## 工具说明

根据全部 wiki.md 和元结构抽取三元组，禁用页面默认不参与图谱生成。

## 适用场景

- Wiki Agent 需要判断页面是否应更新。
- 页面依赖文件发生变化，需要生成草稿。
- 需要抽取图谱或执行诊断建议。
- 需要根据用户文件目录生成 Wiki 页面候选。

## 输入说明

- 输入参数以工具实现为准。
- 页面只解释业务含义，稳定标识保留原始形态。

## 输出说明

- 输出状态、候选页面、草稿或图谱数据。
- 不直接绕过草稿和发布机制。

## 注意事项

- 锁定或禁用页面禁止更新和修复。
- 禁用页面默认不参与图谱生成。
- 用户文件夹建页不作用于系统源码目录。

## 关联页面

- [[Wiki 治理工具箱|tool/wiki]]
- [[系统页面更新技能|skill/wiki/system_file_update]]
- [[用户文件建页技能|skill/wiki/user_file_generation]]
- [[知识图谱抽取技能|skill/wiki/graph_extraction]]
- [[诊断修复技能|skill/wiki/diagnosis_repair]]

## 版本信息

- 当前版本：v1
- 最近发布：待发布
- 最近修改人：系统
- 版本来源：Git
