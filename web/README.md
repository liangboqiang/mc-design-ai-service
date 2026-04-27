# NoteGraph Web

前端只调用一个原子动作面：

```text
/app/action/{action}
```

`web/src/manifest.json` 定义样式与脚本顺序；`scripts/build_web.py` 负责构建离线可运行的 `web/dist`。
