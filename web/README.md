# Wiki App Web

本目录为单仓直连版前端源码。运行时由根目录 `__main__.py` 使用 Python 构建为 `web/dist` 并托管到同一个 18080 端口。

前端不使用 React、Vite、MCP SDK 或独立端口；运行时只请求：

```text
/app/wiki/action/{action}
```
