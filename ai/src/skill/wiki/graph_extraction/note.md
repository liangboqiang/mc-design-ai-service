---
id: skill/wiki/graph_extraction
kind: Skill
status: published
maturity: projectable
lens: lens.skill
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 技能：知识图谱抽取技能

摘要：根据全部 wiki.md 和元结构自动形成三元组，禁用页面默认不参与图谱。

## 基本信息

- 实体类型：技能
- 实体名称：知识图谱抽取技能
- 唯一标识：skill/wiki/graph_extraction
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：知识图谱抽取技能、Wiki Agent、中文 Wiki、真相治理
- 别名：知识图谱抽取技能、skill/wiki/graph_extraction
- 风险等级：中
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

根据全部 wiki.md 和元结构自动形成三元组，禁用页面默认不参与图谱。

## 使用工具

- [[抽取知识图谱|tool/wiki/extract_knowledge_graph]]
- [[页面局部关系|tool/wiki/page_scope_relations]]
- [[检查页面元结构|tool/wiki/check_page_schema]]

## 执行流程

- 读取全部页面。
- 抽取实体类型、链接、作用范围和局部关系。
- 形成三元组。
- 写入图谱读模型。

## 下级技能

- 待补充

## 安全边界

- 不允许生成 Runtime YAML。
- 不允许直接修改真相文件。
- 写操作必须先生成草稿或候选结果。
- 锁定页面和禁用页面禁止自动更新和修复。
- 禁用页面默认不参与知识图谱生成。
- 发布必须由用户明确授权。

## 关联页面

- [[Wiki 治理工具箱|tool/wiki]]
- [[Wiki 只读工具箱|tool/external/wiki]]
- [[通用页面元结构|wiki/schema/common]]

## 版本信息

- 当前版本：v1
- 最近发布：待发布
- 最近修改人：系统
- 版本来源：Git
