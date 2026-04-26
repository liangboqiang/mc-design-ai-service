# 架构说明

```text
浏览器 Wiki App
  ↓
/app/wiki/action/{action}
  ↓
main_app.py
  ↓
ai/wiki_app/actions.py
  ↓
ai/wiki_app/service.py
  ↓
WikiHub / WikiWorkbench
  ↓
ai/src/wiki + ai/src/tool/wiki + Git/store
```

本版本不包含 MCP 运行路径。MCP 如果未来需要，应作为外部协议适配层另行设计，不应进入 Wiki App 内部调用链路。
