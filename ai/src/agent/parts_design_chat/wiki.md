# 智能体：零部件设计对话智能体

摘要：零部件设计对话智能体是系统中的智能体入口，负责按照中文提示词和工具治理规则完成任务。

## 基本信息

- 实体类型：智能体
- 实体名称：零部件设计对话智能体
- 唯一标识：parts_design_chat
- 当前状态：可用
- 锁定状态：未锁定
- 禁用状态：未禁用
- 最近更新：2026-04-25
- 根技能：skill/parts_design/root
- 可用工具箱：design_report、cloude、nx、files、shell、textops、refs、inspect、normalize、wiki、todo、task、compact、workspace、background、subagent
- 模型服务：mock
- 模型名称：mock
- 最大上下文长度：22000
- 工具权限等级：发布
- 允许工具分类：data_processing、local_compute、document、report、enterprise_api、remote_api、cad、engine、workspace_io、text、wiki_read、task、todo、workspace
- 禁止工具分类：external_mcp
- 禁止工具：shell.run

## 元词条

- 关键词：零部件设计对话智能体、parts_design_chat、中文 Wiki、真相治理
- 别名：零部件设计对话智能体、parts_design_chat
- 风险等级：高
- 作用范围：当前页面及直接关联对象
- 局部关系：见关联页面
- 依赖文件：同目录相关文件
- 更新策略：差异化更新

## 智能体使命

零部件设计对话智能体负责以中文提示词和系统工具完成对应范围内的任务。

## 能力范围

- 理解用户需求并进行任务拆解。
- 按需检索 Wiki 页面和工具说明。
- 调用被授权的工具完成确定性操作。
- 输出中文结果并说明依据。

## 安全边界

- 不允许绕过工具权限。
- 不允许伪造工具执行结果。
- 不允许直接修改真相文件。

## 关联页面

- [[零部件设计根技能|skill/parts_design/root]]

## 版本信息

- 当前版本：v1
- 最近发布：待发布
- 最近修改人：系统
- 版本来源：Git
