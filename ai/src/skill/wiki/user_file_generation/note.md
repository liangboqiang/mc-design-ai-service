---
id: skill/wiki/user_file_generation
kind: Skill
status: published
maturity: projectable
lens: lens.skill
source_refs:
  - legacy.wiki.compat
tags:
  - migrated
---

# 技能：用户文件建页技能

摘要：面向用户文件目录自底向上生成 wiki.md 候选页面，空目录和纯下级目录不自动建页。

## 基本信息

- 实体类型：技能
- 实体名称：用户文件建页技能
- 唯一标识：skill/wiki/user_file_generation
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：用户文件建页技能、Wiki Agent、中文 Wiki、真相治理
- 别名：用户文件建页技能、skill/wiki/user_file_generation
- 风险等级：中
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

面向用户文件目录自底向上生成 wiki.md 候选页面，空目录和纯下级目录不自动建页。

## 使用工具

- [[用户文件夹建页|tool/wiki/generate_user_folder_wikis]]
- [[读取页面元结构|tool/wiki/read_schema]]
- [[检查页面元结构|tool/wiki/check_page_schema]]

## 执行流程

- 从底层目录向上处理。
- 下层目录已有 wiki.md 时引用该页面。
- 目录只有子目录且没有直接文件时不生成。
- 系统源码目录不自动生成。

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
