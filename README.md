# Wiki Workbench V3.3 Tile Portal

单仓、单端口、内部函数直连版 Wiki Workbench。

## V3.3 重点

- 去除外置大块浏览器式搜索区域。
- 使用集成式页面命令区，让搜索/页面命令不喧宾夺主。
- 首页改为磁贴门户：历史详情页、知识图谱、后台中心、用户中心。
- 首页辅助词条放在组合检索器下方，采用下拉可激活按钮。
- 页面详情字段改为图标式紧凑展示，减少字段描述占位。
- 保留搜索结果页批量治理、详情页单页治理、图谱、后台中心、用户中心闭环。

## 运行链路

```text
browser
  ↓
/app/wiki/action/{action}
  ↓
main_app.py
  ↓
ai/wiki_app/actions.py
  ↓
ai/wiki_app/service.py
  ↓
WikiHub / WikiWorkbench / user_files
```

## 启动

```bash
python __main__.py --rebuild-web
```

## 检查

```bash
python __main__.py --check
```

访问：

```text
http://127.0.0.1:18080/
```
