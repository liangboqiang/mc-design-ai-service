# Action Contract

系统只有一个动作面：

```text
POST /app/action/{action}
GET  /app/actions
```

请求体必须是 JSON 对象。成功响应：

```json
{
  "ok": true,
  "namespace": "app",
  "action": "graphpedia_search",
  "data": {}
}
```

失败响应：

```json
{
  "ok": false,
  "namespace": "app",
  "action": "graphpedia_search",
  "error": {
    "code": "ACTION_ERROR",
    "message": "错误说明",
    "type": "ValueError"
  }
}
```

动作按对象命名，保持原子、显式、可审计：

```text
graphpedia_search
memory_read_note_detail
notebook_list
workspace_read_file
soft_schema_discover
governance_issue_list
version_commit_notes
```
