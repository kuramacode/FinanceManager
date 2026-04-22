"""Context builders for page-aware AI actions."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from typing import Any

from app.ai.actions import AIActionDefinition, normalize_page_key
from app.i18n import get_language_context
from app.models import db
from app.models.transactions import Transactions
from app.services.accounts import AccountService
from app.services.budget_services.budgets import BudgetService
from app.services.category import Category_Service
from sqlalchemy import text


MAX_CONTEXT_TRANSACTIONS = 120
MAX_CONTEXT_RATES = 30


def _to_float(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value


def _parse_exchange_rate_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text_value = str(value or "").strip()
    if not text_value:
        return None

    try:
        if len(text_value) == 10 and text_value[4] == "-" and text_value[7] == "-":
            year, month, day = text_value.split("-")
            return date(int(year), int(month), int(day))

        if len(text_value) == 10 and text_value[2] == "." and text_value[5] == ".":
            day, month, year = text_value.split(".")
            return date(int(year), int(month), int(day))
    except ValueError:
        return None

    return None


def _load_categories(user_id: int) -> list[dict[str, Any]]:
    try:
        rows = Category_Service().get_categories(user_id)
    except Exception:
        rows = []

    categories = []
    for row in rows:
        categories.append(
            {
                "id": int(row.get("id") or 0),
                "name": row.get("name") or "Unknown",
                "description": row.get("desc") or "",
                "type": (row.get("type") or "").strip().lower(),
                "built_in": bool(row.get("built_in")),
                "emoji": row.get("emoji") or "",
            }
        )
    return categories


def _load_accounts(user_id: int) -> list[dict[str, Any]]:
    try:
        rows = AccountService().get_accounts(user_id)
    except Exception:
        rows = []

    accounts = []
    for row in rows:
        accounts.append(
            {
                "id": int(row.get("id") or 0),
                "name": row.get("name") or "Unknown",
                "balance": _to_float(row.get("balance")),
                "initial_balance": _to_float(row.get("initial_balance")),
                "transactions_delta": _to_float(row.get("transactions_delta")),
                "status": row.get("status") or "unknown",
                "currency_code": (row.get("currency_code") or "UAH").upper(),
                "type": row.get("type") or "",
                "subtitle": row.get("subtitle") or "",
                "note": row.get("note") or "",
            }
        )
    return accounts


def _load_budgets(user_id: int) -> list[dict[str, Any]]:
    try:
        rows = BudgetService().get_budgets(user_id)
    except Exception:
        rows = []

    budgets = []
    for row in rows:
        budgets.append(
            {
                "id": int(row.get("id") or 0),
                "name": row.get("name") or "Untitled budget",
                "description": row.get("desc") or "",
                "amount_limit": _to_float(row.get("amount_limit")),
                "currency_code": (row.get("currency_code") or "UAH").upper(),
                "period_type": row.get("period_type") or "",
                "start_date": _json_safe(row.get("start_date")),
                "end_date": _json_safe(row.get("end_date")),
                "period_start": _json_safe(row.get("period_start")),
                "period_end": _json_safe(row.get("period_end")),
                "spent": _to_float(row.get("spent")),
                "remaining": _to_float(row.get("remaining")),
                "percent": _to_float(row.get("percent")),
                "status": row.get("status") or "unknown",
                "is_active": bool(row.get("is_active")),
                "conversion_error": row.get("conversion_error") or "",
                "categories": [
                    {
                        "id": int(category.get("id") or 0),
                        "name": category.get("name") or "Unknown",
                    }
                    for category in (row.get("categories") or [])
                ],
            }
        )
    return budgets


def _load_transactions(
    user_id: int,
    category_map: dict[int, dict[str, Any]],
    account_map: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = (
        Transactions.query.filter_by(user_id=user_id)
        .order_by(Transactions.date.desc())
        .limit(MAX_CONTEXT_TRANSACTIONS)
        .all()
    )

    transactions = []
    for tx in rows:
        category = category_map.get(int(tx.category_id or 0), {})
        account = account_map.get(int(tx.account_id or 0), {}) if tx.account_id is not None else {}
        currency_code = (
            (tx.currency_code or "").strip().upper()
            or str(account.get("currency_code") or "").strip().upper()
            or "UAH"
        )
        transactions.append(
            {
                "id": int(tx.id),
                "amount": _to_float(tx.amount),
                "date": tx.date.isoformat(timespec="minutes") if tx.date else "",
                "description": tx.description or "",
                "type": (tx.type or "expense").strip().lower(),
                "category_id": int(tx.category_id or 0),
                "category_name": category.get("name") or "Unknown",
                "account_id": None if tx.account_id is None else int(tx.account_id),
                "account_name": account.get("name") or "",
                "currency_code": currency_code,
            }
        )
    return transactions


def _load_exchange_rates() -> list[dict[str, Any]]:
    rows = db.session.execute(
        text(
            """
            SELECT base_code, target_code, rate, date, source
            FROM exchange_rates
            """
        )
    )

    exchange_rates = []
    for row in rows.mappings():
        parsed_date = _parse_exchange_rate_date(row.get("date"))
        exchange_rates.append(
            {
                "base_code": row.get("base_code") or "UAH",
                "target_code": row.get("target_code") or "",
                "rate": _to_float(row.get("rate")),
                "date": parsed_date.isoformat() if parsed_date else str(row.get("date") or ""),
                "source": row.get("source") or "",
            }
        )

    exchange_rates.sort(key=lambda item: (item["date"], item["target_code"]), reverse=True)
    return exchange_rates[:MAX_CONTEXT_RATES]


def _build_totals(transactions: list[dict[str, Any]]) -> dict[str, float]:
    income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    expense = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    transfer = sum(tx["amount"] for tx in transactions if tx["type"] == "transfer")
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "transfer": round(transfer, 2),
        "balance": round(income - expense, 2),
    }


def _build_category_stats(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"amount": 0.0, "transactions_count": 0}
    )

    for tx in transactions:
        key = (tx["category_name"], tx["type"])
        bucket[key]["amount"] += tx["amount"]
        bucket[key]["transactions_count"] += 1

    stats = [
        {
            "name": name,
            "type": tx_type,
            "amount": round(data["amount"], 2),
            "transactions_count": data["transactions_count"],
        }
        for (name, tx_type), data in bucket.items()
    ]
    stats.sort(key=lambda item: item["amount"], reverse=True)
    return stats[:20]


def _build_account_stats(transactions: list[dict[str, Any]], accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tx_count = Counter(tx["account_id"] for tx in transactions if tx["account_id"] is not None)
    by_id = {account["id"]: account for account in accounts}
    stats = []
    for account_id, count in tx_count.items():
        account = by_id.get(int(account_id), {})
        stats.append(
            {
                "id": account_id,
                "name": account.get("name") or "Unknown",
                "transactions_count": count,
                "balance": account.get("balance", 0.0),
                "currency_code": account.get("currency_code", "UAH"),
            }
        )
    stats.sort(key=lambda item: item["transactions_count"], reverse=True)
    return stats


def _build_monthly_history(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0, "transfer": 0.0})
    for tx in transactions:
        month = (tx.get("date") or "")[:7] or "unknown"
        tx_type = tx.get("type") or "expense"
        if tx_type in bucket[month]:
            bucket[month][tx_type] += tx["amount"]

    history = []
    for month, data in sorted(bucket.items()):
        history.append(
            {
                "month": month,
                "income": round(data["income"], 2),
                "expense": round(data["expense"], 2),
                "transfer": round(data["transfer"], 2),
                "balance": round(data["income"] - data["expense"], 2),
            }
        )
    return history


def _build_budget_summary(budgets: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(budget.get("status") or "unknown" for budget in budgets)
    active = [budget for budget in budgets if budget.get("is_active")]
    pressure = sorted(active, key=lambda budget: _to_float(budget.get("percent")), reverse=True)
    return {
        "count": len(budgets),
        "active_count": len(active),
        "status_counts": dict(statuses),
        "highest_pressure": pressure[:5],
    }


def build_ai_action_context(
    *,
    user_id: int,
    action: AIActionDefinition,
    page_key: str | None,
    language: str | None = None,
    user_message: str | None = None,
) -> dict[str, Any]:
    page = normalize_page_key(page_key or action.page)
    categories = _load_categories(user_id)
    accounts = _load_accounts(user_id)
    budgets = _load_budgets(user_id)

    category_map = {category["id"]: category for category in categories}
    account_map = {account["id"]: account for account in accounts}
    transactions = _load_transactions(user_id, category_map, account_map)
    exchange_rates = _load_exchange_rates()

    totals = _build_totals(transactions)
    category_stats = _build_category_stats(transactions)
    account_stats = _build_account_stats(transactions, accounts)
    monthly_history = _build_monthly_history(transactions)

    return _json_safe(
        {
            "response_language": get_language_context(language),
            "selected_action": {
                "id": action.id,
                "page": action.page,
                "title": action.title,
                "description": action.description,
                "scenario_prompt": action.prompt,
                "prompt_type": action.prompt_type,
            },
            "current_page": {
                "key": page,
                "is_action_native_to_page": action.page == page,
            },
            "user_message": (user_message or "").strip(),
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "limits": {
                "transactions_included": len(transactions),
                "max_transactions": MAX_CONTEXT_TRANSACTIONS,
                "exchange_rates_included": len(exchange_rates),
            },
            "summary": {
                "totals": totals,
                "transactions_count": len(transactions),
                "categories_count": len(categories),
                "accounts_count": len(accounts),
                "budgets": _build_budget_summary(budgets),
                "primary_currency": _pick_primary_currency(transactions, accounts, budgets),
            },
            "page_data": {
                "transactions": transactions,
                "categories": categories,
                "category_stats": category_stats,
                "accounts": accounts,
                "account_stats": account_stats,
                "budgets": budgets,
                "monthly_history": monthly_history,
                "exchange_rates": exchange_rates,
            },
        }
    )


def _pick_primary_currency(
    transactions: list[dict[str, Any]],
    accounts: list[dict[str, Any]],
    budgets: list[dict[str, Any]],
) -> str:
    counter = Counter()

    for tx in transactions:
        counter[tx["currency_code"]] += 2
    for account in accounts:
        counter[account["currency_code"]] += 1
    for budget in budgets:
        counter[budget["currency_code"]] += 1

    if counter:
        return counter.most_common(1)[0][0]
    return "UAH"
