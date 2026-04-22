from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit

from flask import has_request_context, request

from app.i18n.translations import (
    DEFAULT_LANGUAGE,
    LANGUAGE_COOKIE_NAME,
    SUPPORTED_LANGUAGES,
    TRANSLATIONS,
)

_MONTHS = {
    "en": {
        "wide": [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        "short": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    },
    "uk": {
        "wide": [
            "січень",
            "лютий",
            "березень",
            "квітень",
            "травень",
            "червень",
            "липень",
            "серпень",
            "вересень",
            "жовтень",
            "листопад",
            "грудень",
        ],
        "short": ["січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру"],
    },
}


def normalize_language(value: str | None) -> str | None:
    if not value:
        return None
    language = value.strip().lower()
    if language in SUPPORTED_LANGUAGES:
        return language
    if "-" in language:
        language = language.split("-", 1)[0]
    return language if language in SUPPORTED_LANGUAGES else None


def get_current_language() -> str:
    if not has_request_context():
        return DEFAULT_LANGUAGE

    query_language = normalize_language(request.args.get("lang"))
    if query_language:
        return query_language

    header_language = normalize_language(request.headers.get("X-Ledger-Language"))
    if header_language:
        return header_language

    cookie_language = normalize_language(request.cookies.get(LANGUAGE_COOKIE_NAME))
    if cookie_language:
        return cookie_language

    accepted = getattr(request, "accept_languages", None)
    if accepted:
        match = accepted.best_match(list(SUPPORTED_LANGUAGES))
        normalized = normalize_language(match)
        if normalized:
            return normalized

    return DEFAULT_LANGUAGE


def get_current_locale() -> str:
    return SUPPORTED_LANGUAGES[get_current_language()]["locale"]


def get_language_context(language: str | None = None) -> dict[str, str]:
    normalized = normalize_language(language) or get_current_language()
    metadata = SUPPORTED_LANGUAGES[normalized]
    return {
        "language": normalized,
        "locale": metadata["locale"],
        "label": metadata["label"],
        "native": metadata["native"],
        "ai_instruction": translate_for_language(normalized, "ai.response_language_instruction"),
    }


def _lookup(catalog: dict[str, Any], key: str) -> Any:
    value: Any = catalog
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def translate(key: str, **kwargs: Any) -> str:
    language = get_current_language()
    value = _lookup(TRANSLATIONS.get(language, {}), key)
    if value is None:
        value = _lookup(TRANSLATIONS[DEFAULT_LANGUAGE], key)
    if value is None:
        return key
    if isinstance(value, dict):
        return key
    if kwargs:
        try:
            return str(value).format(**kwargs)
        except (KeyError, ValueError):
            return str(value)
    return str(value)


def translate_for_language(language: str, key: str, **kwargs: Any) -> str:
    normalized = normalize_language(language) or DEFAULT_LANGUAGE
    value = _lookup(TRANSLATIONS.get(normalized, {}), key)
    if value is None:
        value = _lookup(TRANSLATIONS[DEFAULT_LANGUAGE], key)
    if value is None or isinstance(value, dict):
        return key
    if kwargs:
        try:
            return str(value).format(**kwargs)
        except (KeyError, ValueError):
            return str(value)
    return str(value)


def merge_catalogs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_catalogs(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def get_client_i18n() -> dict[str, Any]:
    language = get_current_language()
    return {
        "language": language,
        "locale": SUPPORTED_LANGUAGES[language]["locale"],
        "translations": merge_catalogs(TRANSLATIONS[DEFAULT_LANGUAGE], TRANSLATIONS.get(language, {})),
    }


def format_month(month: int | str, *, short: bool = False, language: str | None = None) -> str:
    try:
        index = int(month) - 1
    except (TypeError, ValueError):
        return str(month)
    if index < 0 or index > 11:
        return str(month)

    lang = normalize_language(language) or get_current_language()
    width = "short" if short else "wide"
    return _MONTHS.get(lang, _MONTHS[DEFAULT_LANGUAGE])[width][index]


def format_month_year(value: date | datetime | None = None) -> str:
    current = value or datetime.now()
    return f"{format_month(current.month)} {current.year}"


def format_short_date(value: date | datetime) -> str:
    return f"{format_month(value.month, short=True)} {value.day}"


def format_date_range(start: datetime, end: datetime) -> str:
    if start.date() == end.date():
        return f"{format_short_date(start)}, {start.year}"
    return f"{format_short_date(start)}, {start.year} - {format_short_date(end)}, {end.year}"


def is_safe_redirect_target(target: str | None) -> bool:
    if not target:
        return False

    ref = urlsplit(target)
    if ref.scheme or ref.netloc:
        host_url = urlsplit(request.host_url)
        return ref.scheme in {"http", "https"} and ref.netloc == host_url.netloc
    return target.startswith("/")


def register_i18n(app) -> None:
    @app.context_processor
    def inject_i18n_context():
        language = get_current_language()
        return {
            "_": translate,
            "t": translate,
            "current_language": language,
            "current_locale": SUPPORTED_LANGUAGES[language]["locale"],
            "current_language_name": SUPPORTED_LANGUAGES[language]["native"],
            "available_languages": SUPPORTED_LANGUAGES,
            "client_i18n": get_client_i18n(),
        }

    app.jinja_env.globals["t"] = translate
    app.jinja_env.globals["_"] = translate
    app.jinja_env.globals["current_language"] = get_current_language


def set_language_cookie(response, language: str):
    response.set_cookie(
        LANGUAGE_COOKIE_NAME,
        language,
        max_age=60 * 60 * 24 * 365,
        samesite="Lax",
    )
    return response
