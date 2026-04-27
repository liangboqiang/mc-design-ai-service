from __future__ import annotations



class AnthropicClient:
    def __init__(self, model: str, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("Anthropic-compatible API key is required.")
        if not base_url:
            raise ValueError("Anthropic-compatible base_url is required.")
        self.model = model
        self.api_key = api_key
        self.url = f"{base_url.rstrip('/')}/v1/messages"

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": messages,
        }
        import requests
        response = requests.post(
            self.url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        return "\n".join(
            part.get("text", "")
            for part in data.get("content", [])
            if part.get("type") == "text"
        )
