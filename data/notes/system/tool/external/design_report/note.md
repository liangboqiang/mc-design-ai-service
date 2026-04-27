---
id: tool/external/design_report
kind: Toolbox
status: published
maturity: projectable
lens: lens.default
source_refs:
  - memory.native.migrated
tags:
  - migrated
---

# 工具箱：设计报告工具箱

摘要：设计报告工具箱用于组织一组可被智能体调用的能力，页面采用中文格式描述工具集合、边界和版本信息。

## 基本信息

- 实体类型：工具箱
- 实体名称：设计报告工具箱
- 唯一标识：design_report
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25
- 模块路径：tool.external.design_report.toolbox
- 类名称：DesignReportToolbox
- 所属分类：外部

## 元词条

- 关键词：设计报告工具箱、design_report、Memory Note、真相治理
- 别名：设计报告工具箱、design_report
- 风险等级：中
- 作用范围：当前页面及直接关联对象
- 局部关系：见关联页面
- 依赖文件：同目录相关文件
- 更新策略：差异化更新

## 工具箱说明

设计报告工具箱用于组织一组相关工具。工具箱页面只描述能力集合和边界，具体执行由工具实现负责。

## 包含工具

- [[列出报告|tool/external/design_report/list_reports]]
- [[创建报告图片|tool/external/design_report/create_image]]
- [[创建设计报告|tool/external/design_report/create_report]]
- [[导出报告|tool/external/design_report/export_report]]
- [[更新设计报告|tool/external/design_report/update_report]]
- [[获取报告详情|tool/external/design_report/get_report_detail]]

## 使用边界

- 工具箱只提供能力集合说明，不直接执行业务任务。
- 高风险能力必须通过权限和发布流程治理。

## 关联页面

- [[创建设计报告|tool/external/design_report/create_report]]
- [[获取报告详情|tool/external/design_report/get_report_detail]]
- [[更新设计报告|tool/external/design_report/update_report]]
- [[列出报告|tool/external/design_report/list_reports]]
- [[导出报告|tool/external/design_report/export_report]]
- [[创建报告图片|tool/external/design_report/create_image]]

## 版本信息

- 当前版本：v1
- 最近发布：待发布
- 最近修改人：系统
- 版本来源：Git
