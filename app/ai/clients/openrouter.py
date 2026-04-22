"""OpenRouter provider module."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import requests

from app.ai.config import (
    AIConfig,
    AIConnectionSettings,
    normalize_openrouter_base_url,
    normalize_openrouter_model,
)
from app.ai.exceptions import AIClientError, AIConfigurationError


@dataclass(frozen=True)
class OpenRouterMessage:
    role: str
    content: str

    def model_dump(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass(frozen=True)
class OpenRouterCompletion:
    content: str
    raw: Mapping[str, Any]


class OpenRouterClient:
    """Small OpenRouter chat-completions client for app AI use cases."""

    def __init__(
        self,
        settings: AIConnectionSettings | None = None,
        session: requests.Session | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout: int | float | None = None,
    ) -> None:
        resolved = settings or AIConfig.settings()

        if api_key is not None or model_name is not None or base_url is not None or timeout is not None:
            resolved = AIConnectionSettings(
                provider=resolved.provider,
                api_key=api_key or resolved.api_key,
                model=normalize_openrouter_model(model_name or resolved.model),
                base_url=normalize_openrouter_base_url(base_url or resolved.base_url),
                timeout_seconds=int(timeout or resolved.timeout_seconds),
                max_completion_tokens=resolved.max_completion_tokens,
                temperature=resolved.temperature,
                site_url=resolved.site_url,
                app_title=resolved.app_title,
            )

        self.settings = resolved
        self.session = session or requests.Session()

        if not self.settings.api_key:
            raise AIConfigurationError("OPENROUTER_API_KEY is not configured")

    @property
    def chat_completions_url(self) -> str:
        base_url = self.settings.base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }

        if self.settings.site_url:
            headers["HTTP-Referer"] = self.settings.site_url

        if self.settings.app_title:
            headers["X-Title"] = self.settings.app_title

        return headers

    def complete(
        self,
        messages: Iterable[OpenRouterMessage | Mapping[str, str]],
        *,
        json_response: bool = False,
    ) -> OpenRouterCompletion:
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": [self._message_to_dict(message) for message in messages],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_completion_tokens,
        }

        if json_response:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = self.session.post(
                self.chat_completions_url,
                headers=self._headers(),
                json=payload,
                timeout=self.settings.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise AIClientError(f"AI request failed: {exc}") from exc

        if response.status_code >= 400:
            raise AIClientError(self._format_provider_error(response))

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise AIClientError("Provider returned invalid JSON response") from exc

        return OpenRouterCompletion(
            content=self._extract_message_content(data),
            raw=data,
        )

    def send_prompt(self, prompt: str, *, json_response: bool = False) -> str:
        completion = self.complete(
            [OpenRouterMessage(role="user", content=prompt)],
            json_response=json_response,
        )
        return completion.content

    @staticmethod
    def _message_to_dict(message: OpenRouterMessage | Mapping[str, str]) -> dict[str, str]:
        if isinstance(message, OpenRouterMessage):
            return message.model_dump()

        return {
            "role": str(message.get("role", "")),
            "content": str(message.get("content", "")),
        }

    @staticmethod
    def _extract_message_content(data: Mapping[str, Any]) -> str:
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise AIClientError(f"Unexpected provider response format: {data}") from exc

    @staticmethod
    def _format_provider_error(response: requests.Response) -> str:
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError):
            payload = None

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or "").strip()
                code = error.get("code")
                if message:
                    if code:
                        return f"Provider returned {response.status_code} ({code}): {message}"
                    return f"Provider returned {response.status_code}: {message}"

        detail = response.text.strip()
        content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
        if response.status_code == 404 and (
            detail.lower().startswith("<!doctype html") or "text/html" in content_type.lower()
        ):
            return (
                "Provider returned 404 HTML. Check OPENROUTER_BASE_URL: it must be "
                "https://openrouter.ai/api/v1, not an OpenRouter model page URL."
            )

        if len(detail) > 800:
            detail = f"{detail[:800]}..."
        return f"Provider returned {response.status_code}: {detail}"
