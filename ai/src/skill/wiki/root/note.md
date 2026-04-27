---
id: skill/wiki/root
kind: Skill
status: published
maturity: projectable
lens: lens.skill
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 技能：Wiki 治理根技能

摘要：统一调度 Wiki Agent 的检索、阅读、页面诊断、中文元结构治理、依赖更新、用户文件建页、图谱抽取、草稿审查和回滚辅助。

## 基本信息

- 实体类型：技能
- 实体名称：Wiki 治理根技能
- 唯一标识：skill/wiki/root
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：Wiki 治理根技能、Wiki Agent、中文 Wiki、真相治理
- 别名：Wiki 治理根技能、skill/wiki/root
- 风险等级：中
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

统一调度 Wiki Agent 的检索、阅读、页面诊断、中文元结构治理、依赖更新、用户文件建页、图谱抽取、草稿审查和回滚辅助。

## 使用工具

- [[Wiki 检索|tool/external/wiki/search]]
- [[读取 Wiki 页面|tool/external/wiki/read_page]]
- [[读取 Wiki 源文|tool/external/wiki/read_source]]
- [[Wiki 问答|tool/external/wiki/answer]]
- [[读取页面元结构|tool/wiki/read_schema]]
- [[检查页面元结构|tool/wiki/check_page_schema]]
- [[解析页面链接|tool/wiki/resolve_page_links]]
- [[查询别名索引|tool/wiki/alias_query]]
- [[诊断页面问题|tool/wiki/diagnose_page]]

## 执行流程

- 识别任务类型。
- 选择下级技能。
- 优先读取元结构和页面真相。
- 所有写操作先生成草稿。
- 发布必须等待用户明确授权。

## 下级技能

- [[检索阅读技能|skill/wiki/search_read]]
- [[页面诊断技能|skill/wiki/page_diagnosis]]
- [[元结构治理技能|skill/wiki/schema_governance]]
- [[页面重写技能|skill/wiki/page_rewrite]]
- [[链接治理技能|skill/wiki/link_governance]]
- [[系统页面更新技能|skill/wiki/system_file_update]]
- [[用户文件建页技能|skill/wiki/user_file_generation]]
- [[依赖变化更新技能|skill/wiki/dependency_update]]
- [[版本审查技能|skill/wiki/version_review]]
- [[草稿发布审查技能|skill/wiki/draft_publish_review]]
- [[回滚辅助技能|skill/wiki/rollback_assist]]
- [[知识图谱抽取技能|skill/wiki/graph_extraction]]
- [[图谱增强检索技能|skill/wiki/graph_search]]
- [[诊断修复技能|skill/wiki/diagnosis_repair]]
- [[批量治理技能|skill/wiki/batch_governance]]

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
