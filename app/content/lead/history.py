from __future__ import annotations

from collections import OrderedDict
from math import ceil

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required

from app.i18n import format_date_range, format_month, get_current_language, translate as t
from app.models import Accounts, Categories, Transactions
from app.utils.main_scripts import get_userid, get_username

_history = Blueprint("history", __name__)

HISTORY_TYPES = {"all", "income", "expense", "transfer"}
PER_PAGE = 25

_WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "uk": ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"],
}


def _normalize_type(value: str | None) -> str:
    selected = (value or "all").strip().lower()
    return selected if selected in HISTORY_TYPES else "all"


def _normalize_page(value: str | None) -> int:
    try:
        page = int(value or 1)
    except (TypeError, ValueError):
        return 1
    return max(page, 1)


def _type_label(type_name: str) -> str:
    return t(f"common.types.{type_name}") if type_name in {"income", "expense", "transfer"} else t("common.types.all")


def _format_amount(amount: float, type_name: str) -> dict[str, str]:
    value = abs(float(amount or 0.0))
    if type_name == "income":
        return {"text": f"+{value:.2f}", "class": "pos"}
    if type_name == "expense":
        return {"text": f"-{value:.2f}", "class": "neg"}
    return {"text": f"{value:.2f}", "class": "neutral"}


def _date_label(value) -> dict[str, str]:
    if not value:
        return {"title": t("common.unknown_date"), "subtitle": ""}

    language = get_current_language()
    weekdays = _WEEKDAYS.get(language, _WEEKDAYS["en"])
    return {
        "title": f"{format_month(value.month, language=language)} {value.day}",
        "subtitle": weekdays[value.weekday()],
    }


def _build_summary(records: list[dict]) -> dict:
    income_total = sum(item["amount"] for item in records if item["type"] == "income")
    expense_total = sum(item["amount"] for item in records if item["type"] == "expense")
    return {
        "count": len(records),
        "income_total": income_total,
        "expense_total": expense_total,
        "net_total": income_total - expense_total,
    }


def _build_records(user_id: int) -> list[dict]:
    categories = {
        category.id: category
        for category in Categories.query.filter_by(user_id=user_id).all()
    }
    accounts = {
        account.id: account
        for account in Accounts.query.filter_by(user_id=user_id).all()
    }

    transactions = (
        Transactions.query.filter_by(user_id=user_id)
        .order_by(Transactions.date.desc(), Transactions.id.desc())
        .all()
    )

    records = []
    for transaction in transactions:
        type_name = (transaction.type or "expense").strip().lower()
        category = categories.get(transaction.category_id)
        account = accounts.get(transaction.account_id) if transaction.account_id is not None else None
        amount = float(transaction.amount or 0.0)
        formatted_amount = _format_amount(amount, type_name)

        records.append(
            {
                "id": transaction.id,
                "amount": amount,
                "amount_text": formatted_amount["text"],
                "amount_class": formatted_amount["class"],
                "account_name": account.name if account else t("transactions.no_account"),
                "category_name": category.name if category else t("common.unknown_category"),
                "currency_code": (transaction.currency_code or "").upper() or "UAH",
                "date": transaction.date,
                "description": transaction.description or t("common.untitled_transaction"),
                "emoji": category.emoji if category and category.emoji else "#",
                "status": t("history.status_done"),
                "type": type_name,
                "type_label": _type_label(type_name),
            }
        )

    return records


def _matches_search(record: dict, query: str) -> bool:
    if not query:
        return True

    haystack = " ".join(
        str(record.get(key) or "")
        for key in ("description", "account_name", "category_name", "currency_code", "type_label")
    ).lower()
    return query.lower() in haystack


def _filter_records(records: list[dict], selected_type: str, query: str) -> list[dict]:
    return [
        record
        for record in records
        if (selected_type == "all" or record["type"] == selected_type) and _matches_search(record, query)
    ]


def _group_records(records: list[dict]) -> list[dict]:
    grouped = OrderedDict()
    for record in records:
        key = record["date"].date() if record["date"] else None
        if key not in grouped:
            grouped[key] = {
                "date": _date_label(record["date"]),
                "records": [],
                "total": 0.0,
            }
        grouped[key]["records"].append(record)
        if record["type"] == "income":
            grouped[key]["total"] += record["amount"]
        elif record["type"] == "expense":
            grouped[key]["total"] -= record["amount"]

    result = []
    for group in grouped.values():
        total = group["total"]
        group["total_text"] = f"{total:+.2f}" if total else "0.00"
        group["total_class"] = "pos" if total > 0 else "neg" if total < 0 else "neutral"
        result.append(group)
    return result


def _date_range_label(records: list[dict]) -> str:
    dates = [record["date"] for record in records if record["date"]]
    if not dates:
        return t("transactions.no_dates")
    return format_date_range(min(dates), max(dates))


def _page_url(page: int, selected_type: str, query: str) -> str:
    values = {"page": page}
    if selected_type != "all":
        values["type"] = selected_type
    if query:
        values["q"] = query
    return url_for("history.history", **values)


@_history.route("/history")
@login_required
def history():
    """Renders the transaction history timeline."""
    user_id = get_userid()
    selected_type = _normalize_type(request.args.get("type"))
    search_query = (request.args.get("q") or "").strip()
    page = _normalize_page(request.args.get("page"))

    all_records = _build_records(user_id)
    filtered_records = _filter_records(all_records, selected_type, search_query)
    total_pages = max(ceil(len(filtered_records) / PER_PAGE), 1)
    page = min(page, total_pages)

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    visible_records = filtered_records[start:end]

    return render_template(
        "history.html",
        username=get_username(),
        userID=user_id,
        active_page="history",
        selected_type=selected_type,
        search_query=search_query,
        summary=_build_summary(filtered_records),
        date_range_label=_date_range_label(filtered_records),
        history_groups=_group_records(visible_records),
        page=page,
        total_pages=total_pages,
        total_records=len(filtered_records),
        page_start=start + 1 if filtered_records else 0,
        page_end=min(end, len(filtered_records)),
        page_url=lambda target_page: _page_url(target_page, selected_type, search_query),
    )
