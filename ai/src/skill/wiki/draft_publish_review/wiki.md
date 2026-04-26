# 技能：草稿发布审查技能

摘要：审查草稿差异、页面元结构、链接和真相状态；只有用户明确授权时才发布。

## 基本信息

- 实体类型：技能
- 实体名称：草稿发布审查技能
- 唯一标识：skill/wiki/draft_publish_review
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：草稿发布审查技能、Wiki Agent、中文 Wiki、真相治理
- 别名：草稿发布审查技能、skill/wiki/draft_publish_review
- 风险等级：高
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

审查草稿差异、页面元结构、链接和真相状态；只有用户明确授权时才发布。

## 使用工具

- [[草稿差异查看|tool/wiki/diff_draft]]
- [[检查页面元结构|tool/wiki/check_page_schema]]
- [[解析页面链接|tool/wiki/resolve_page_links]]
- [[真相状态检查|tool/wiki/check_truth_status]]
- [[发布历史查询|tool/wiki/release_history]]
- [[发布草稿|tool/wiki/publish_draft]]

## 执行流程

- 查看草稿差异。
- 检查页面元结构。
- 检查链接和真相状态。
- 生成发布建议。
- 用户明确授权后发布。

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
