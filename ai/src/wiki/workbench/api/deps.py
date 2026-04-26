from __future__ import annotations

import os
from pathlib import Path
from wiki.workbench import WikiWorkbench

def get_workbench() -> WikiWorkbench:
    return WikiWorkbench(Path(os.getenv("DESIGN_AGENTS_PROJECT_ROOT", ".")).resolve())
