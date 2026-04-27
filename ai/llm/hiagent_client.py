from __future__ import annotations

import json
import os
import ssl
from typing import Any


class HiAgentClient:
    """Client for the user's HiAgent-style model service.

    Supported modes:
    1. Proxy mode:
       - base_url is the full /ai-assistant endpoint, or the API prefix/root.
       - POST {"query": "..."}.

    2. Direct HiAgent mode:
       - CHAT_QUERY_URL creates AppConversationID.
       - CREATE_CONVERSATION_URL sends chat_query_v2.
       - Headers use Apikey.
    """

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None):
        self.model = model or "hiagent"
        self.api_key = (api_key or os.getenv("HIAGENT_API_KEY") or "").strip()
        self.base_url = (base_url or os.getenv("HIAGENT_PROXY_URL") or os.getenv("HIAGENT_BASE_URL") or "").strip().rstrip("/")
        self.create_conversation_url = (
            os.getenv("CREATE_CONVERSATION_URL")
            or os.getenv("HIAGENT_CREATE_CONVERSATION_URL")
            or ""
        ).strip()
        self.chat_query_url = (
            os.getenv("CHAT_QUERY_URL")
            or os.getenv("HIAGENT_CHAT_QUERY_URL")
            or ""
        ).strip()
        self.user_id = (os.getenv("CHAT_USER_ID") or os.getenv("HIAGENT_CHAT_USER_ID") or "default_user").strip()
        self.api_prefix = (os.getenv("API_PREFIX") or "/mc-design/ai-api").strip().strip("/")
        self.verify_ssl = (os.getenv("HIAGENT_VERIFY_SSL") or "false").strip().lower() in {"1", "true", "yes"}
        self.timeout_init = float(os.getenv("HIAGENT_INIT_TIMEOUT", "60"))
        self.timeout_chat = float(os.getenv("HIAGENT_CHAT_TIMEOUT", "600"))
        self._conversation_id: str | None = None
        self._session = None

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        query = self._build_query(system_prompt, messages)
        if self.base_url:
            return self._call_proxy(query)
        return self._call_direct(query)

    def _build_query(self, system_prompt: str, messages: list[dict]) -> str:
        rows = ["# System Prompt", str(system_prompt or "").strip(), "", "# Conversation"]
        for item in messages or []:
            role = str(item.get("role") or "user")
            content = str(item.get("content") or "")
            rows.append(f"\n## {role}\n{content}")
        return "\n".join(rows).strip()

    def _call_proxy(self, query: str) -> str:
        import requests

        url = self._proxy_url()
        response = requests.post(url, json={"query": query}, timeout=self.timeout_chat)
        response.raise_for_status()
        return self._extract_answer(response.json())

    def _proxy_url(self) -> str:
        if self.base_url.endswith("/ai-assistant"):
            return self.base_url
        if self.base_url.endswith("/dictAssistant"):
            return f"{self.base_url}/ai-assistant"
        if self.base_url.endswith(self.api_prefix):
            return f"{self.base_url}/dictAssistant/ai-assistant"
        return f"{self.base_url}/{self.api_prefix}/dictAssistant/ai-assistant"

    def _call_direct(self, query: str) -> str:
        if not self.api_key:
            raise ValueError("hiagent provider requires HIAGENT_API_KEY or api_key when base_url/proxy is not used.")
        if not self.create_conversation_url:
            raise ValueError("hiagent provider requires CREATE_CONVERSATION_URL for direct mode.")
        if not self.chat_query_url:
            raise ValueError("hiagent provider requires CHAT_QUERY_URL for direct mode.")

        conversation_id = self._conversation_id or self._get_conversation_id()
        self._conversation_id = conversation_id
        headers = {
            "Apikey": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "Query": query,
            "AppConversationID": conversation_id,
            "ResponseMode": "blocking",
            "UserID": self.user_id,
        }
        response = self._session_post(self.create_conversation_url, headers=headers, json_payload=payload, timeout=self.timeout_chat)
        try:
            response.raise_for_status()
        except Exception:
            self._conversation_id = None
            raise
        return self._extract_answer(response.json())

    def _get_conversation_id(self) -> str:
        headers = {
            "Apikey": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "Inputs": {},
            "UserID": self.user_id,
        }
        response = self._session_post(self.chat_query_url, headers=headers, json_payload=payload, timeout=self.timeout_init)
        response.raise_for_status()
        result = response.json()
        conversation = result.get("Conversation") if isinstance(result, dict) else None
        conversation_id = conversation.get("AppConversationID") if isinstance(conversation, dict) else None
        if not conversation_id:
            raise ValueError(f"Failed to initialize HiAgent conversation. Response: {result}")
        return str(conversation_id)

    def _session_post(self, url: str, *, headers: dict[str, str], json_payload: dict[str, Any], timeout: float):
        session = self._session_obj()
        return session.post(url, headers=headers, json=json_payload, timeout=timeout, verify=self.verify_ssl)

    def _session_obj(self):
        if self._session is not None:
            return self._session

        import requests
        import urllib3
        from requests.adapters import HTTPAdapter
        from urllib3.util.ssl_ import create_urllib3_context

        class LegacySSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):  # noqa: ANN001
                context = create_urllib3_context()
                try:
                    context.minimum_version = ssl.TLSVersion.TLSv1_1
                except Exception:  # noqa: BLE001
                    pass
                try:
                    context.set_ciphers("ALL")
                except Exception:  # noqa: BLE001
                    pass
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                kwargs["ssl_context"] = context
                return super().init_poolmanager(*args, **kwargs)

        session = requests.Session()
        session.mount("https://", LegacySSLAdapter())
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self._session = session
        return session

    def _extract_answer(self, payload: Any) -> str:
        if isinstance(payload, str):
            return payload

        for path in (
            ("Answer",),
            ("answer",),
            ("Response",),
            ("response",),
            ("Result",),
            ("result",),
            ("Text",),
            ("text",),
            ("Content",),
            ("content",),
            ("Data", "Answer"),
            ("Data", "answer"),
            ("data", "answer"),
            ("data", "text"),
            ("Output", "Text"),
            ("output", "text"),
        ):
            value = self._get_path(payload, path)
            if isinstance(value, str) and value.strip():
                return value

        # Some services return a list of message chunks.
        for key in ("Messages", "messages", "Outputs", "outputs"):
            value = payload.get(key) if isinstance(payload, dict) else None
            if isinstance(value, list):
                texts = [self._extract_answer(item) for item in value]
                texts = [text for text in texts if text and not text.strip().startswith("{")]
                if texts:
                    return "\n".join(texts)

        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _get_path(payload: Any, path: tuple[str, ...]) -> Any:
        current = payload
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current
