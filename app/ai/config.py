"""AI provider configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "inclusionai/ling-2.6-flash:free"


def _load_env_files() -> None:
    for env_path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "app" / ".env"):
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


_load_env_files()


def _clean(value: str | None) -> str:
    return (value or "").strip().strip('"').strip("'")


def _env(
    environ: Mapping[str, str],
    *names: str,
    default: str = "",
) -> str:
    for name in names:
        value = _clean(environ.get(name))
        if value:
            return value
    return default


def _env_int(
    environ: Mapping[str, str],
    *names: str,
    default: int,
) -> int:
    raw_value = _env(environ, *names, default=str(default))
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _env_float(
    environ: Mapping[str, str],
    *names: str,
    default: float,
) -> float:
    raw_value = _env(environ, *names, default=str(default))
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def normalize_openrouter_base_url(value: str | None) -> str:
    base_url = _clean(value).rstrip("/")
    if not base_url:
        return DEFAULT_OPENROUTER_BASE_URL

    if base_url.endswith("/chat/completions"):
        return base_url[: -len("/chat/completions")]

    if base_url.startswith("https://openrouter.ai/") and "/api/" not in base_url:
        return DEFAULT_OPENROUTER_BASE_URL

    return base_url


def normalize_openrouter_model(value: str | None) -> str:
    model = _clean(value)
    if not model:
        return DEFAULT_OPENROUTER_MODEL

    parsed = urlparse(model)
    if parsed.netloc == "openrouter.ai" and parsed.path:
        path = parsed.path.strip("/")
        if path and not path.startswith("api/"):
            return path

    return model


@dataclass(frozen=True)
class AIConnectionSettings:
    provider: str
    api_key: str
    model: str
    base_url: str
    timeout_seconds: int
    max_completion_tokens: int
    temperature: float
    site_url: str = ""
    app_title: str = "Finance Manager"


def load_ai_settings(environ: Mapping[str, str] | None = None) -> AIConnectionSettings:
    env = environ or os.environ

    return AIConnectionSettings(
        provider="openrouter",
        api_key=_env(env, "OPENROUTER_API_KEY"),
        model=normalize_openrouter_model(
            _env(
                env,
                "OPENROUTER_MODEL",
                "AI_MODEL_NAME",
                "MODEL_NAME",
                default=DEFAULT_OPENROUTER_MODEL,
            )
        ),
        base_url=normalize_openrouter_base_url(
            _env(env, "OPENROUTER_BASE_URL", default=DEFAULT_OPENROUTER_BASE_URL)
        ),
        timeout_seconds=_env_int(env, "AI_TIMEOUT_SECONDS", "TIMEOUT_SECONDS", default=60),
        max_completion_tokens=_env_int(
            env,
            "AI_MAX_COMPLETION_TOKENS",
            "MAX_COMPLETION_TOKENS",
            default=800,
        ),
        temperature=_env_float(env, "AI_TEMPERATURE", "TEMPERATURE", default=0.2),
        site_url=_env(env, "OPENROUTER_SITE_URL", "APP_URL"),
        app_title=_env(env, "OPENROUTER_APP_TITLE", "APP_TITLE", default="Finance Manager"),
    )


class AIConfig:
    """Backward-compatible facade for older imports."""

    PROVIDER_NAME = "openrouter"

    @staticmethod
    def settings() -> AIConnectionSettings:
        return load_ai_settings()

    _settings = load_ai_settings()
    MODEL_NAME = _settings.model
    API_KEY = _settings.api_key
    BASE_URL = _settings.base_url
    TIMEOUT_SECONDS = _settings.timeout_seconds
    MAX_COMPLETION_TOKENS = _settings.max_completion_tokens
    TEMPERATURE = _settings.temperature
