# Action Contract

唯一前后端交互入口：

```text
POST /app/wiki/action/{action}
```

成功响应：

```json
{
  "ok": true,
  "action": "wiki_search",
  "data": []
}
```

失败响应：

```json
{
  "ok": false,
  "action": "wiki_read_page",
  "error": {
    "code": "MISSING_REQUIRED_PARAM",
    "message": "缺少必要参数：page_id"
  }
}
```
