from __future__ import annotations

from fastapi import FastAPI
from .version_api import router as version_router

app = FastAPI(title="Wiki Workbench Version API")
app.include_router(version_router, prefix="/api/wiki")
