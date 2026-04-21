from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required

from app.i18n import format_date_range, translate as t
from app.models import db
from app.models.transactions import Transactions
from app.services.accounts import AccountService
from app.services.category import Category_Service
from app.utils.main_scripts import get_userid, get_username

_transactions = Blueprint("transactions", __name__)

account_service = AccountService()
category_service = Category_Service()
TRANSACTION_TYPES = {"income", "expense", "transfer"}


def _normalize_filter(value: str | None) -> str:
    """Очищає значення фільтра, зводить його до нижнього регістру та залишає лише дозволений тип або `all`."""
    value = (value or "all").strip().lower()
    return value if value in {"all", *TRANSACTION_TYPES} else "all"


def _redirect_with_feedback(status: str, message: str, filter_value: str | None = None):
    """Повертає редірект на сторінку списку з повідомленням про результат дії та, за потреби, збереженим фільтром."""
    params = {
        "status": status,
        "message": message,
    }
    normalized_filter = _normalize_filter(filter_value)
    if normalized_filter != "all":
        params["filter"] = normalized_filter
    return redirect(url_for("transactions.transactions", **params))


def _load_reference_data(user_id: int):
    """Завантажує категорії й рахунки користувача та будує словники для швидкого доступу за ідентифікатором."""
    categories = category_service.get_categories(user_id)
    accounts = account_service.get_accounts(user_id)

    category_map = {int(category["id"]): category for category in categories}
    account_map = {int(account["id"]): account for account in accounts}

    return categories, accounts, category_map, account_map


def _normalize_transaction(transaction, category_map: dict[int, dict], account_map: dict[int, dict]):
    """Перетворює модель транзакції на словник для шаблону, підставляючи назву категорії, рахунок і валюту за замовчуванням."""
    category = category_map.get(transaction.category_id, {})
    account = account_map.get(transaction.account_id, {}) if transaction.account_id is not None else {}
    currency_code = (
        (transaction.currency_code or "").strip().upper()
        or str(account.get("currency_code") or "").strip().upper()
        or "UAH"
    )

    return {
        "id": transaction.id,
        "amount": float(transaction.amount or 0.0),
        "date": transaction.date.isoformat(timespec="minutes") if transaction.date else "",
        "description": transaction.description or "",
        "type": (transaction.type or "expense").strip().lower(),
        "category_id": transaction.category_id,
        "category_name": category.get("name") or t("common.unknown_category"),
        "category_emoji": category.get("emoji") or "#",
        "account_id": transaction.account_id,
        "account_name": account.get("name") or "",
        "account_emoji": account.get("emoji") or "",
        "currency_code": currency_code,
    }


def _parse_datetime(date_value: str | None, time_value: str | None) -> datetime:
    """Перевіряє формат дати й часу з форми та об’єднує їх в один об’єкт `datetime`."""
    date_value = (date_value or "").strip()
    time_value = (time_value or "").strip()

    if not date_value:
        raise ValueError(t("errors.date_required"))

    try:
        parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(t("errors.date_format")) from exc

    if time_value:
        try:
            parsed_time = datetime.strptime(time_value, "%H:%M").time()
        except ValueError as exc:
            raise ValueError(t("errors.time_format")) from exc
    else:
        parsed_time = datetime.min.time()

    return datetime.combine(parsed_date, parsed_time)


def _parse_transaction_payload(user_id: int, form):
    """Зчитує поля форми, перевіряє суму, тип, категорію, рахунок і валюту та повертає нормалізований payload."""
    categories, accounts, category_map, account_map = _load_reference_data(user_id)

    if not categories:
        raise ValueError(t("errors.create_category_first"))

    try:
        amount = float(form.get("amount") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(t("errors.amount_number")) from exc

    if amount <= 0:
        raise ValueError(t("errors.amount_positive"))

    description = (form.get("description") or "").strip()
    type_ = (form.get("type") or "").strip().lower()
    if type_ not in TRANSACTION_TYPES:
        raise ValueError(t("errors.transaction_type"))

    try:
        category_id = int(form.get("category_id") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(t("errors.valid_category")) from exc

    category = category_map.get(category_id)
    if category is None:
        raise ValueError(t("errors.category_unavailable"))
    if (category.get("type") or "").strip().lower() != type_:
        raise ValueError(t("errors.category_type_mismatch"))

    account_id = None
    account_raw = (form.get("account_id") or "").strip()
    if account_raw:
        try:
            account_id = int(account_raw)
        except ValueError as exc:
            raise ValueError(t("errors.valid_account")) from exc

        if account_id not in account_map:
            raise ValueError(t("errors.account_unavailable"))

    currency_code = (form.get("currency_code") or "").strip().upper()
    if not currency_code and account_id is not None:
        currency_code = str(account_map[account_id].get("currency_code") or "").strip().upper()
    if not currency_code:
        currency_code = "UAH"
    if len(currency_code) != 3 or not currency_code.isalpha():
        raise ValueError(t("errors.currency_code"))

    date_value = _parse_datetime(form.get("date"), form.get("time"))

    return {
        "amount": round(amount, 2),
        "date": date_value,
        "description": description or None,
        "category_id": category_id,
        "type": type_,
        "account_id": account_id,
        "currency_code": currency_code,
    }


def _build_transactions_summary(transactions_data: list[dict]) -> dict:
    """Підраховує кількість операцій і окремі підсумки для доходів, витрат, переказів та чистого результату."""
    income_total = round(
        sum(transaction["amount"] for transaction in transactions_data if transaction["type"] == "income"),
        2,
    )
    expense_total = round(
        sum(transaction["amount"] for transaction in transactions_data if transaction["type"] == "expense"),
        2,
    )
    transfer_total = round(
        sum(transaction["amount"] for transaction in transactions_data if transaction["type"] == "transfer"),
        2,
    )

    return {
        "count": len(transactions_data),
        "income_total": income_total,
        "expense_total": expense_total,
        "transfer_total": transfer_total,
        "net_total": round(income_total - expense_total, 2),
    }


def _build_date_range_label(transactions_data: list[dict]) -> str:
    """Формує зручний для інтерфейсу підпис з мінімальною та максимальною датою у поточному списку."""
    dates = []
    for transaction in transactions_data:
        if not transaction.get("date"):
            continue
        try:
            dates.append(datetime.fromisoformat(transaction["date"]))
        except ValueError:
            continue

    if not dates:
        return t("transactions.no_dates")

    start = min(dates)
    end = max(dates)
    if start.date() == end.date():
        return format_date_range(start, start)
    return format_date_range(start, end)


@_transactions.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    """Обробляє відображення списку, створення, редагування та видалення транзакцій поточного користувача."""
    user_id = get_userid()

    if request.method == "POST":
        action = (request.form.get("action") or "create").strip().lower()
        return_filter = request.form.get("return_filter")

        try:
            if action == "delete":
                transaction_id = int(request.form.get("transaction_id") or 0)
                transaction = db.session.get(Transactions, transaction_id)
                if transaction is None or transaction.user_id != user_id:
                    raise ValueError(t("errors.transaction_not_found"))

                db.session.delete(transaction)
                db.session.commit()
                return _redirect_with_feedback("success", t("errors.transaction_deleted"), return_filter)

            if action not in {"create", "update"}:
                raise ValueError(t("errors.unsupported_transaction_action"))

            payload = _parse_transaction_payload(user_id, request.form)

            if action == "create":
                transaction = Transactions(user_id=user_id, **payload)
                db.session.add(transaction)
                db.session.commit()
                return _redirect_with_feedback("success", t("errors.transaction_created"), return_filter)

            transaction_id = int(request.form.get("transaction_id") or 0)
            transaction = db.session.get(Transactions, transaction_id)
            if transaction is None or transaction.user_id != user_id:
                raise ValueError(t("errors.transaction_not_found"))

            for field, value in payload.items():
                setattr(transaction, field, value)

            db.session.commit()
            return _redirect_with_feedback("success", t("errors.transaction_updated"), return_filter)
        except ValueError as exc:
            db.session.rollback()
            return _redirect_with_feedback("error", str(exc), return_filter)

    initial_filter = _normalize_filter(request.args.get("filter"))
    feedback_status = (request.args.get("status") or "").strip().lower()
    if feedback_status not in {"success", "error"}:
        feedback_status = ""
    feedback_message = (request.args.get("message") or "").strip()

    categories, accounts, category_map, account_map = _load_reference_data(user_id)
    transactions_data = [
        _normalize_transaction(transaction, category_map, account_map)
        for transaction in Transactions.query.filter_by(user_id=user_id).order_by(Transactions.date.desc()).all()
    ]
    summary = _build_transactions_summary(transactions_data)

    return render_template(
        "transactions.html",
        transactions_data=transactions_data,
        categories_data=categories,
        accounts_data=accounts,
        summary=summary,
        date_range_label=_build_date_range_label(transactions_data),
        initial_filter=initial_filter,
        feedback_status=feedback_status,
        feedback_message=feedback_message,
        username=get_username(),
        userID=user_id,
        active_page="transactions",
    )
