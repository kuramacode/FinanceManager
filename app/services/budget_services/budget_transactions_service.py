import sqlite3
from app.utils.main_scripts import _db_path


class BudgetConversionError(RuntimeError):
    pass


def _build_converter():
    from app.cache.rate import RateCache
    from app.services.converter import CurrencyConverter

    return CurrencyConverter(RateCache())


def _normalize_query_date(value):
    return value.isoformat() if hasattr(value, "isoformat") else value



def sum_transactions_for_budget(
    user_id,
    categories: list[int],
    date_from,
    date_to,
    budget_currency_code: str,
    converter=None,
) -> float:
    if not categories:
        return 0.0

    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        placeholders = ",".join("?" for _ in categories)
        transaction_type = "expense"

        query = f'''
        SELECT amount, currency_code
        FROM transactions
        WHERE user_id=?
        AND type=?
        AND category_id IN ({placeholders})
        AND DATE(date) BETWEEN DATE(?) AND DATE(?)
        '''

        params = [user_id, transaction_type, *categories, date_from, date_to]
        cur.execute(query, params)

        transactions = cur.fetchall()

    budget_currency_code = (budget_currency_code or "").upper()
    total_amount = 0.0

    for transaction in transactions:
        amount = float(transaction["amount"] or 0.0)
        transaction_currency = (transaction["currency_code"] or budget_currency_code).upper()

        if not budget_currency_code or transaction_currency == budget_currency_code:
            total_amount += amount
            continue

        if converter is None:
            converter = _build_converter()

        try:
            converted = converter.convert(
                base_currency=transaction_currency,
                target_currency=budget_currency_code,
                amount=amount,
            )
        except Exception as exc:
            raise BudgetConversionError(
                f"Failed to convert {transaction_currency} to {budget_currency_code}"
            ) from exc
            
        total_amount += float(converted["result"] or 0.0)

    return round(total_amount, 2)