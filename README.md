# mc-design-ai-service

Memory-Native NoteGraph 原子系统版本。

本版本完成了系统性收束：前后端只通过一个稳定动作面协作，知识入口以 **图谱百科 / 记事本 / 笔记详情 / 审核治理** 四个页面组织，`note.md` 仍是唯一真相。

## 当前运行入口

```text
/app/actions
/app/action/{action}
```

前端不再感知 Memory / Workbench 分裂路由；后端通过 `ai/app/actions.py` 维护唯一动作目录。

## 核心目录

```text
ai/app          原子动作面与 HTTP 外壳
ai/memory       Evidence / NoteStore / Lens / Graph / MemoryView / Proposal
ai/workbench    记事本、文件、审核、版本、发布、诊断
ai/capability   CapabilitySpec / CapabilityView / Surface / Dispatcher
ai/kernel       Kernel 主循环、Prompt、Profile、Session
web/src         NoteGraph 中文前端源代码
web/dist        离线可运行构建产物
data/notes      note.md 唯一知识真相
data/config     记事本、仓库、软模式配置
```

## 检查

```bash
python scripts/build_web.py
python scripts/check_frontend.py
python scripts/check_no_legacy_core.py
python scripts/check_backend.py
```

## 启动

```bash
python __main__.py --rebuild-web
```
