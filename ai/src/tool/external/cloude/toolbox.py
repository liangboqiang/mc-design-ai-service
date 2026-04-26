from __future__ import annotations

import json
import os
import ssl
from pathlib import Path
from typing import Any

class CloudeToolbox:
    """Enterprise cloud API toolbox migrated from the old external MCP toolbox."""

    toolbox_name = "cloude"
    tags = ("external", "enterprise_api", "cloud")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "CloudeToolbox":
        return CloudeToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "cloude.connect_qpp": self._exec_connect_qpp,
            "cloude.query_ecr_list": self._exec_query_ecr_list,
            "cloude.query_ipm_list": self._exec_query_ipm_list,
        }

    def _exec_connect_qpp(self, args: dict):
        return self._connect_qpp(args)

    def _exec_query_ecr_list(self, args: dict):
        return self._post_json(os.getenv("ECR_URL", ""), self._filter_none(args), default_error="ECR_URL is not configured.")

    def _exec_query_ipm_list(self, args: dict):
        return self._post_json(os.getenv("IPM_URL", ""), self._filter_none(args), default_error="IPM_URL is not configured.")

    def _connect_qpp(self, args: dict) -> str:
        base_url = os.getenv("QPP_URL", "")
        if not base_url:
            return json.dumps({"ok": False, "data": None, "message": "QPP_URL is not configured."}, ensure_ascii=False, indent=2)
        payload = {
            "Worker": args.get("worker") or args.get("Worker") or args.get("user_id") or (self.runtime.settings.user_id if self.runtime else ""),
            "StartDate": args.get("StartDate") or args.get("start_date") or "",
        }
        result = self._request_json(base_url, payload)
        if not result.get("ok"):
            return json.dumps(result, ensure_ascii=False, indent=2)
        data = result.get("data")
        try:
            val = data.get("Val") if isinstance(data, dict) else data
            if isinstance(val, list):
                status_map = {
                    1: "编制中",
                    2: "校对中",
                    3: "审核中",
                    4: "标准化中",
                    5: "批准中",
                    6: "已完成",
                }
                for row in val:
                    if isinstance(row, dict) and "Status" in row:
                        row["StatusText"] = status_map.get(row.get("Status"), str(row.get("Status")))
                return json.dumps({"ok": True, "data": val, "message": "连接QPP成功"}, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return json.dumps({"ok": True, "data": data, "message": "连接QPP成功"}, ensure_ascii=False, indent=2)

    def _post_json(self, url: str, payload: dict[str, Any], *, default_error: str) -> str:
        if not url:
            return json.dumps({"ok": False, "data": None, "message": default_error}, ensure_ascii=False, indent=2)
        return json.dumps(self._request_json(url, payload), ensure_ascii=False, indent=2)

    def _request_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        import requests
        from requests.adapters import HTTPAdapter

        class LegacyTLSAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):  # noqa: ANN001
                context = ssl.create_default_context()
                try:
                    context.minimum_version = ssl.TLSVersion.TLSv1
                    context.set_ciphers("DEFAULT@SECLEVEL=1")
                except Exception:
                    pass
                kwargs["ssl_context"] = context
                return super().init_poolmanager(*args, **kwargs)

        session = requests.Session()
        session.mount("https://", LegacyTLSAdapter())
        try:
            response = session.post(
                url,
                data=json.dumps(payload, ensure_ascii=False),
                headers={"Content-Type": "application/json"},
                timeout=float(os.getenv("CLOUDE_API_TIMEOUT", "30")),
            )
            response.raise_for_status()
            text = response.content.decode("utf-8")
            try:
                data = json.loads(text)
            except Exception:
                data = text
            return {"ok": True, "data": data, "message": "调用成功"}
        except requests.exceptions.SSLError as exc:
            return {"ok": False, "data": None, "message": f"SSL握手失败: {exc}"}
        except requests.exceptions.RequestException as exc:
            return {"ok": False, "data": None, "message": f"网络请求失败: {exc}"}
        except Exception as exc:
            return {"ok": False, "data": None, "message": f"系统内部错误: {exc}"}
        finally:
            session.close()

    @staticmethod
    def _filter_none(args: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in dict(args or {}).items() if v is not None}
