from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask_login import current_user

from app.models import db
from app.models.transactions import Transactions
from app.models.categories import Categories

def _to_float(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0
    
def _parse_date(value: Optional[str], default: Optional[datetime] = None) -> Optional[datetime]:
    if not value:
        return default
    
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {value}")

def _serialize_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")

def _get_user_currency() -> str:
    return "UAH"

def collect_transactions_for_period(user_id: int, date_from: datetime, date_to: datetime) -> List[Transactions]:
    return (
        db.session.query(Transactions)
        .filter(Transactions.user_id == user_id)
        .filter(Transactions.date >= date_from)
        .filter(Transactions.date <= date_to)
        .all()
    )
    
def get_category_map() -> dict[int, str]:
    categories = db.session.query(Categories.id, Categories.name).all()
    return {category_id: name for category_id, name in categories}
    
def build_category_stats(transactions: list, tx_type: str) -> list[dict[str, Any]]:
    """
    Собирает топ категорий по сумме для указанного типа транзакций.
    """
    if tx_type not in ("income", "expense"):
        raise ValueError("tx_type must be 'income' or 'expense'")

    category_map = get_category_map()
    bucket = defaultdict(lambda: {"amount": 0.0, "transactions_count": 0})

    for tx in transactions:
        transaction_type = getattr(tx, "type", None)
        if transaction_type != tx_type:
            continue

        amount = _to_float(getattr(tx, "amount", 0))
        category_id = getattr(tx, "category_id", None)
        category_name = category_map.get(category_id, "Unknown")

        bucket[category_name]["amount"] += amount
        bucket[category_name]["transactions_count"] += 1

    stats = []
    for category_name, data in bucket.items():
        stats.append(
            {
                "name": category_name,
                "amount": round(data["amount"], 2),
                "transactions_count": data["transactions_count"],
            }
        )

    stats.sort(key=lambda item: item["amount"], reverse=True)
    return stats[:5]

def build_totals(transactions: List[Transactions]) -> Dict[str, float]:
    income = 0.0
    expense = 0.0

    for tx in transactions:
        amount = _to_float(getattr(tx, "amount", 0))
        tx_type = getattr(tx, "type", None)

        if tx_type == "income":
            income += amount
        elif tx_type == "expense":
            expense += amount

    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
    }


def build_expense_analysis_context(
    user_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    today = datetime.utcnow()
    default_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    default_end = today.replace(hour=23, minute=59, second=59, microsecond=0)

    start_dt = _parse_date(date_from, default=default_start)
    end_dt = _parse_date(date_to, default=default_end)

    if start_dt is None or end_dt is None:
        raise ValueError("date_from and date_to cannot be None")

    if start_dt > end_dt:
        raise ValueError("date_from cannot be greater than date_to")

    transactions = collect_transactions_for_period(
        user_id=user_id,
        date_from=start_dt,
        date_to=end_dt,
    )

    totals = build_totals(transactions)

    return {
        "period": {
            "date_from": _serialize_date(start_dt),
            "date_to": _serialize_date(end_dt),
        },
        "totals": totals,
        "top_expense_categories": build_category_stats(transactions, "expense"),
        "top_income_categories": build_category_stats(transactions, "income"),
        "transactions_count": len(transactions),
        "currency": _get_user_currency(),
    }