from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
SRC = WEB / "src"
DIST = WEB / "dist"
ASSETS_SRC = SRC / "assets"
ASSETS_DIST = DIST / "assets"
VENDOR_SRC = WEB / "vendor"
VENDOR_DIST = DIST / "vendor"
STAMP = DIST / ".wiki_app_build.json"


def source_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(SRC.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(SRC).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _inline_index() -> str:
    css = (ASSETS_SRC / "style.css").read_text(encoding="utf-8")
    js = (ASSETS_SRC / "app.js").read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise RuntimeError("app.js 中包含 </script>，不能安全内联。")
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Wiki Workbench</title>
    <style>
{css}
    </style>
  </head>
  <body>
    <div id="root">
      <main class="fatal">
        <h1>Wiki Workbench</h1>
        <p>前端正在启动。如果这里一直不变化，请打开浏览器控制台查看错误，或访问 /health 检查后端。</p>
      </main>
    </div>
    <script>
{js}
    </script>
  </body>
</html>
"""


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    ASSETS_DIST.mkdir(parents=True, exist_ok=True)

    # The production page is fully inline to avoid asset mounting, module-script,
    # cache, and dist staleness issues. Assets are still copied for diagnostics.
    (DIST / "index.html").write_text(_inline_index(), encoding="utf-8")

    for path in sorted(ASSETS_SRC.rglob("*")):
        if path.is_file():
            target = ASSETS_DIST / path.relative_to(ASSETS_SRC)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    if VENDOR_SRC.exists():
        for path in sorted(VENDOR_SRC.rglob("*")):
            if path.is_file():
                target = VENDOR_DIST / path.relative_to(VENDOR_SRC)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

    STAMP.write_text(
        json.dumps(
            {
                "source_hash": source_hash(),
                "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mode": "unified-direct-functions-inline",
                "builder": "python-inline",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
    print(f"web built: {DIST}")
