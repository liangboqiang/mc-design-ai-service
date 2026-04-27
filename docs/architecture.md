# NoteGraph 原子架构

当前主线：

```text
Browser
  -> /app/action/{action}
  -> ai/app/actions.py
  -> Memory / Workbench / Capability / Kernel 服务
  -> note.md / Graph Index / Proposal / Version
```

核心边界：

- App 只负责 HTTP、静态资源和一个原子动作面。
- 前端只调用 `/app/action/{action}`，不再区分兼容路由或历史命名空间。
- Memory 是唯一知识状态层，`note.md` 是唯一人机知识真相。
- Graph 是从 `note.md` 构建的索引，不是真相本身。
- Workbench 负责记事本、源文件、审核治理、版本、发布和回退。
- Capability 负责可执行能力表面和工具执行。
- Kernel 负责运行循环与智能生成，但智能结果必须先进入 Proposal。

页面模型：

```text
图谱百科 -> 统一检索与图谱索引
记事本   -> 系统笔记本、源文件、软模式、抽取规则
笔记详情 -> note.md 主体阅读、编辑、版本、局部图谱
审核治理 -> 健康检查、问题节点、修复建议、批量治理
```
