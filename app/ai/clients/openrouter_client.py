"""OpenRouter-compatible client."""

import json
from typing import Any, Dict

import requests

from app.ai.config import AIConfig
from app.ai.exceptions import AIClientError, AIConfigurationError, AIResponseFormatError

class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout: int | float | None = None,
    ) -> None: 
        self.api_key = api_key or AIConfig.API_KEY
        self.model_name = model_name or AIConfig.MODEL_NAME
        self.base_url = (base_url or AIConfig.BASE_URL).rstrip("/")
        self.timeout = timeout or AIConfig.TIMEOUT_SECONDS
        
        if not self.api_key:
            raise AIConfigurationError("OPENROUTER_API_KEY is not configured")

    def _chat_completions_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"
        
    def send_prompt(self, prompt: str) -> str:
        url = self._chat_completions_url()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": AIConfig.TEMPERATURE,
            "max_tokens": AIConfig.MAX_COMPLETION_TOKENS,
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise AIClientError(f"AI request failed: {exc}") from exc
        
        if response.status_code >= 400:
            raise AIClientError(
                f"Provider returned {response.status_code}: {response.text}"
            )
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise AIClientError("Provider returned invalid JSON response") from exc
        
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIClientError(f"Unexpected provider response format: {data}") from exc
        
