from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from app.models.transactions import Transactions
from app.services.accounts import AccountService
from app.services.budget_services.budgets import BudgetService
from app.services.category import Category_Service

account_service = AccountService()
budget_service = BudgetService()
category_service = Category_Service()


def _serialize_temporal(value):
    """Converts date and datetime values to ISO strings for templates."""
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _normalize_category(category) -> dict:
    """Builds a JSON-safe category payload for analytics widgets."""
    return {
        "id": int(category["id"]),
        "name": category.get("name") or "Unnamed category",
        "desc": category.get("desc") or "",
        "emoji": category.get("emoji") or "#",
        "type": (category.get("type") or "expense").strip().lower(),
        "built_in": bool(category.get("built_in")),
    }


def _normalize_account(account) -> dict:
    """Builds a JSON-safe account payload for analytics widgets."""
    return {
        "id": int(account["id"]),
        "name": account.get("name") or "Unnamed account",
        "balance": float(account.get("balance") or 0.0),
        "initial_balance": float(account.get("initial_balance") or 0.0),
        "transactions_delta": float(account.get("transactions_delta") or 0.0),
        "status": (account.get("status") or "active").strip().lower(),
        "currency_code": (account.get("currency_code") or "UAH").strip().upper(),
        "emoji": account.get("emoji") or "#",
        "type": account.get("type") or "",
        "subtitle": account.get("subtitle") or "",
        "note": account.get("note") or "",
    }


def _normalize_budget(budget) -> dict:
    """Builds a compact budget payload for analytics widgets."""
    categories = []
    for category in budget.get("categories") or []:
        categories.append(
            {
                "id": int(category["id"]),
                "name": category.get("name") or "Unnamed category",
                "emoji": category.get("emoji") or "#",
            }
        )

    return {
        "id": int(budget["id"]),
        "name": budget.get("name") or "Untitled budget",
        "desc": budget.get("desc") or "",
        "amount_limit": float(budget.get("amount_limit") or 0.0),
        "currency_code": (budget.get("currency_code") or "UAH").strip().upper(),
        "period_type": (budget.get("period_type") or "").strip().lower(),
        "start_date": _serialize_temporal(budget.get("start_date")),
        "end_date": _serialize_temporal(budget.get("end_date")),
        "period_start": _serialize_temporal(budget.get("period_start")),
        "period_end": _serialize_temporal(budget.get("period_end")),
        "spent": float(budget.get("spent") or 0.0),
        "remaining": float(budget.get("remaining") or 0.0),
        "percent": float(budget.get("percent") or 0.0),
        "status": (budget.get("status") or "inactive").strip().lower(),
        "is_active": bool(budget.get("is_active")),
        "conversion_error": budget.get("conversion_error") or "",
        "icon": budget.get("icon") or "#",
        "categories": categories,
    }


def _normalize_transaction(transaction, category_map: dict[int, dict], account_map: dict[int, dict]) -> dict:
    """Builds a JSON-safe transaction payload for analytics widgets."""
    category = category_map.get(int(transaction.category_id), {})
    account = account_map.get(int(transaction.account_id), {}) if transaction.account_id is not None else {}
    currency_code = (
        (transaction.currency_code or "").strip().upper()
        or str(account.get("currency_code") or "").strip().upper()
        or "UAH"
    )

    return {
        "id": int(transaction.id),
        "amount": float(transaction.amount or 0.0),
        "date": transaction.date.isoformat(timespec="minutes") if transaction.date else "",
        "description": transaction.description or "",
        "type": (transaction.type or "expense").strip().lower(),
        "category_id": int(transaction.category_id),
        "category_name": category.get("name") or "Unknown category",
        "category_emoji": category.get("emoji") or "#",
        "account_id": None if transaction.account_id is None else int(transaction.account_id),
        "account_name": account.get("name") or "",
        "account_emoji": account.get("emoji") or "",
        "currency_code": currency_code,
    }


def _pick_primary_currency(transactions: list[dict], accounts: list[dict], budgets: list[dict]) -> str:
    """Chooses a default analytics currency without mixing monetary values."""
    counter = Counter()

    for transaction in transactions:
        counter[transaction["currency_code"]] += 2

    for account in accounts:
        if account["status"] == "active":
            counter[account["currency_code"]] += 1

    for budget in budgets:
        counter[budget["currency_code"]] += 1

    if counter:
        return counter.most_common(1)[0][0]
    return "UAH"


def build_analytics_payload(user_id: int) -> dict:
    """Collects real project data required by the analytics page."""
    raw_categories = category_service.get_categories(user_id)
    raw_accounts = account_service.get_accounts(user_id)
    raw_budgets = budget_service.get_budgets(user_id)

    categories = [_normalize_category(category) for category in raw_categories]
    accounts = [_normalize_account(account) for account in raw_accounts]
    budgets = [_normalize_budget(budget) for budget in raw_budgets]

    category_map = {category["id"]: category for category in categories}
    account_map = {account["id"]: account for account in accounts}

    transactions = [
        _normalize_transaction(transaction, category_map, account_map)
        for transaction in Transactions.query.filter_by(user_id=user_id).order_by(Transactions.date.desc()).all()
    ]

    available_currencies = sorted(
        {
            *(transaction["currency_code"] for transaction in transactions),
            *(account["currency_code"] for account in accounts),
            *(budget["currency_code"] for budget in budgets),
        }
    )
    if not available_currencies:
        available_currencies = ["UAH"]

    primary_currency = _pick_primary_currency(transactions, accounts, budgets)
    if primary_currency not in available_currencies:
        primary_currency = available_currencies[0]

    return {
        "transactions": transactions,
        "categories": categories,
        "accounts": accounts,
        "budgets": budgets,
        "available_currencies": available_currencies,
        "primary_currency": primary_currency,
    }
