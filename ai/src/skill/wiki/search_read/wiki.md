# 技能：检索阅读技能

摘要：负责检索 Wiki、读取渲染页面和源文，并用中文整理依据。

## 基本信息

- 实体类型：技能
- 实体名称：检索阅读技能
- 唯一标识：skill/wiki/search_read
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25

## 元词条

- 关键词：检索阅读技能、Wiki Agent、中文 Wiki、真相治理
- 别名：检索阅读技能、skill/wiki/search_read
- 风险等级：中
- 作用范围：Wiki 页面、真实文件、草稿、版本和图谱
- 局部关系：属于 [[Wiki 治理根技能|skill/wiki/root]]
- 依赖文件：相关工具页面和元结构页面
- 更新策略：差异化更新

## 技能目标

负责检索 Wiki、读取渲染页面和源文，并用中文整理依据。

## 使用工具

- [[Wiki 检索|tool/external/wiki/search]]
- [[读取 Wiki 页面|tool/external/wiki/read_page]]
- [[读取 Wiki 源文|tool/external/wiki/read_source]]
- [[Wiki 问答|tool/external/wiki/answer]]
- [[查询别名索引|tool/wiki/alias_query]]
- [[图谱增强检索|tool/wiki/graph_enhanced_search]]

## 执行流程

- 先检索。
- 再读取页面。
- 必要时读取源文。
- 输出中文结论和页面依据。

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
