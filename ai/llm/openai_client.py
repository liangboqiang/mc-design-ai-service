from __future__ import annotations



class OpenAIClient:
    def __init__(self, model: str, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("OpenAI-compatible API key is required.")
        if not base_url:
            raise ValueError("OpenAI-compatible base_url is required.")
        self.model = model
        self.api_key = api_key
        self.url = f"{base_url.rstrip('/')}/chat/completions"

    def complete(self, system_prompt: str, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        }
        import requests
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
