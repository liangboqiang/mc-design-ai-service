---
id: skill/wiki/rollback_assist
kind: Skill
status: published
maturity: projectable
lens: lens.skill
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 技能：回滚辅助技能

摘要：基于历史版本创建回滚草稿，解释回滚影响，不直接覆盖真相文件。

## 基本信息

- 实体类型：技能
- 实体名称：回滚辅助技能
- 唯一标识：skill/wiki/rollback_assist
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：回滚辅助技能、Wiki Agent、中文 Wiki、真相治理
- 别名：回滚辅助技能、skill/wiki/rollback_assist
- 风险等级：中
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

基于历史版本创建回滚草稿，解释回滚影响，不直接覆盖真相文件。

## 使用工具

- [[页面历史查询|tool/wiki/page_history]]
- [[读取历史版本|tool/wiki/read_version]]
- [[版本差异对比|tool/wiki/diff_versions]]
- [[创建回滚草稿|tool/wiki/create_rollback_draft]]
- [[草稿差异查看|tool/wiki/diff_draft]]

## 执行流程

- 选择历史版本。
- 比较当前版本与目标版本。
- 创建回滚草稿。
- 展示差异和影响。

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
