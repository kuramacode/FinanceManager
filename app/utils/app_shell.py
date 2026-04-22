from __future__ import annotations

from copy import deepcopy

from flask import request
from flask_login import current_user

from app.ai.actions import get_ai_actions_for_page, get_ai_page_definition, normalize_page_key
from app.i18n import translate as t


_BLUEPRINT_TO_PAGE = {
    "dashboard": "dashboard",
    "transactions": "transactions",
    "budgets": "budgets",
    "accounts": "accounts",
    "analytics": "analytics",
    "category": "categories",
    "currency": "currency",
    "history": "history",
    "profile": "profile",
}

_PAGE_LABEL_KEYS = {
    "dashboard": "nav.dashboard",
    "transactions": "nav.transactions",
    "budgets": "nav.budgets",
    "accounts": "nav.accounts",
    "analytics": "nav.analytics",
    "category": "nav.categories",
    "categories": "nav.categories",
    "currency": "nav.exchange",
    "history": "nav.history",
    "profile": "nav.personal",
    "generic": "common.app_name",
}

_AI_CAPTION_KEYS = {
    "dashboard": "ai.captions.dashboard",
    "transactions": "ai.captions.transactions",
    "budgets": "ai.captions.budgets",
    "accounts": "ai.captions.accounts",
    "analytics": "ai.captions.analytics",
    "categories": "ai.captions.categories",
    "currency": "ai.captions.currency",
    "history": "ai.captions.history",
    "profile": "ai.captions.profile",
    "generic": "ai.captions.generic",
}


def _resolve_username() -> str:
    if getattr(current_user, "is_authenticated", False):
        return getattr(current_user, "username", "") or t("common.personal")
    return t("common.guest")


def resolve_active_page(endpoint: str | None = None) -> str:
    current_endpoint = endpoint or getattr(request, "endpoint", None) or ""
    blueprint = current_endpoint.split(".", 1)[0]
    return _BLUEPRINT_TO_PAGE.get(blueprint, "generic")


def _translate_ai_action(action: dict) -> dict:
    translated = deepcopy(action)
    action_id = str(action.get("id") or "").strip()
    if not action_id:
        return translated

    for field in ("title", "description", "prompt"):
        key = f"ai.actions.{action_id}.{field}"
        translated[f"{field}_key"] = key
        value = t(key)
        if value != key:
            translated[field] = value

    return translated


def get_ai_entrypoint(page_key: str | None = None) -> dict:
    resolved_key = normalize_page_key(page_key or resolve_active_page())
    page = get_ai_page_definition(resolved_key)

    label = page.label
    label_key = _PAGE_LABEL_KEYS.get(resolved_key)
    if label_key:
        label = t(label_key)

    caption = page.caption
    caption_key = _AI_CAPTION_KEYS.get(resolved_key)
    if caption_key:
        caption = t(caption_key)

    actions = [
        _translate_ai_action(action.model_dump())
        for action in get_ai_actions_for_page(resolved_key)
    ]

    return {
        "key": resolved_key,
        "label": label,
        "caption": caption,
        "connected": True,
        "actions": actions,
    }


def get_app_shell_context() -> dict:
    active_page = resolve_active_page()
    return {
        "app_shell": {
            "active_page": active_page,
            "username": _resolve_username(),
        },
        "ai_entrypoint": get_ai_entrypoint(active_page),
    }
