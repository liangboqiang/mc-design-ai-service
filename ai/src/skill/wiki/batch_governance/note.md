---
id: skill/wiki/batch_governance
kind: Skill
status: published
maturity: projectable
lens: lens.skill
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 技能：批量治理技能

摘要：批量检查和治理 Wiki 页面，优先生成报告和草稿，不直接批量发布。

## 基本信息

- 实体类型：技能
- 实体名称：批量治理技能
- 唯一标识：skill/wiki/batch_governance
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：批量治理技能、Wiki Agent、中文 Wiki、真相治理
- 别名：批量治理技能、skill/wiki/batch_governance
- 风险等级：高
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

批量检查和治理 Wiki 页面，优先生成报告和草稿，不直接批量发布。

## 使用工具

- [[Wiki 检索|tool/external/wiki/search]]
- [[检查页面元结构|tool/wiki/check_page_schema]]
- [[诊断页面问题|tool/wiki/diagnose_page]]
- [[规范化中文页面|tool/wiki/normalize_page_to_chinese]]
- [[抽取知识图谱|tool/wiki/extract_knowledge_graph]]

## 执行流程

- 检索目标范围。
- 逐页诊断。
- 按风险分组。
- 低风险生成草稿。
- 高风险等待人工确认。

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
