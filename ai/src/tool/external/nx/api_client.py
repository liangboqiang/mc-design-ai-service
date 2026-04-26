from __future__ import annotations

import json
import os
from typing import Any


class NXApiClient:
    """HTTP API client for the existing remote NX tool server.

    V22 intentionally does not connect to the old MCP server. It keeps the
    remote NX server contract in API form:
    - base URL: NX_API_BASE_URL / NX_SERVER_BASE_URL
    - endpoint template: NX_API_ENDPOINT_TEMPLATE, default "/{tool_name}"
    - payload: {"user_id": "...", ...original tool args...}
    """

    def __init__(self, *, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("NX_API_BASE_URL") or os.getenv("NX_SERVER_BASE_URL") or "").strip().rstrip("/")
        self.api_key = (api_key or os.getenv("NX_API_KEY") or "").strip()
        self.endpoint_template = (os.getenv("NX_API_ENDPOINT_TEMPLATE") or "/{tool_name}").strip()
        self.timeout = float(os.getenv("NX_API_TIMEOUT", "300"))

    def call(self, tool_name: str, args: dict[str, Any]) -> str:
        if not self.base_url:
            return json.dumps(
                {
                    "ok": False,
                    "data": None,
                    "message": "NX API base URL is not configured. Set NX_API_BASE_URL or NX_SERVER_BASE_URL.",
                    "tool_name": tool_name,
                    "request": args,
                },
                ensure_ascii=False,
                indent=2,
            )
        payload = dict(args or {})
        url = self._url(tool_name)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        import requests

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        try:
            result = response.json()
        except Exception:
            result = {"ok": True, "data": response.text, "message": "NX API returned non-JSON response."}
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _url(self, tool_name: str) -> str:
        endpoint = self.endpoint_template.format(tool_name=tool_name, toolbox="nx")
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"
