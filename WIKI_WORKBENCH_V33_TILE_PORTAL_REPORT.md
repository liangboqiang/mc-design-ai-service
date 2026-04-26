# Wiki Workbench V3.3 Tile Portal Delivery Report

## 基础包

- `wiki_workbench_v32_home_redesign.zip`

## 本次修复的问题

1. 浏览器位置不优雅：
   - 移除首页/搜索页/详情页外置大块浏览器样式。
   - `renderFrame` 使用集成式 `workspace-head + head-command`。
   - 搜索页和详情页使用紧凑命令区，不再占用主内容面积。

2. 首页辅助词条：
   - 辅助检索词条放在首页组合检索器下面。
   - 改为下拉式可激活按钮。
   - 支持多组选词后与基础 query 组合检索。

3. 首页磁贴门户：
   - 首页下方显示 4 个磁贴：
     - 历史详情页
     - 知识图谱
     - 后台中心
     - 用户中心
   - 知识图谱磁贴显示缩略图。
   - 后台中心磁贴显示小型数据看板和全量刷新入口。
   - 用户中心磁贴显示用户治理对话入口。
   - 磁贴带链接跳转元素。

4. 页面字段和描述臃肿：
   - 页面信息框字段改为图标式紧凑行。
   - 缩小页面标题、状态标签、信息行字体和间距。
   - 用图标和短标签替代重复字段说明，减少描述占位。

## 验收结果

```text
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/spreadsheet_warmup.py", line 720, in _warm_feature_flows
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/spreadsheet_warmup.py", line 704, in _warm_collaboration_flows
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/generated/interface/models.py", line 35986, in hydrate_crdt_from_proto
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/rpc/remote.py", line 747, in __call__
  File "/tmp/tmp.vJDWZqkmKn/artifact_tool_v2-2.6.11/presentation_artifact_tool/rpc/client.py", line 150, in call
presentation_artifact_tool.rpc.client.RemoteError: hydrateCrdtFromProto requires an empty collaborative document.
[check] backend
Backend direct-action match rate: 100.0% (7/7)
[check] frontend
Frontend V3.3 tile portal match rate: 100.0% (22/22)
[check] e2e
E2E V3.3 closed-loop rate: 100.0% (15/15)
[check] blueprint
Problem fix rate: 100.0% (17/17)
Architecture elegance score: 100.0%
[check] cleanup
Old redundancy cleanup rate: 100.0% (20/20)
Functional closed-loop rate: 100.0% (9/9)

```

## 启动

```bash
python __main__.py --rebuild-web
```

## 检查

```bash
python __main__.py --check
```

## 访问

```text
http://127.0.0.1:18080/
```
