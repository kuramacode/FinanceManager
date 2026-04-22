from datetime import datetime, timedelta

import sqlite3

from app.services.exchange_rates import (
    fetch_latest_rates,
    load_latest_rate_records,
    load_rate_records_for_date,
    parse_rate_date,
)
from app.utils.main_scripts import _db_path


def _preferred_rate_date(value: str):
    nbu_publish_time = datetime(
        datetime.now().year,
        datetime.now().month,
        datetime.now().day,
        15,
        30,
    )
    current_time = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")

    if nbu_publish_time > current_time:
        return (datetime.now() - timedelta(days=1)).date()
    return current_time.date()


def get_rates(date: str, currencies: list):
    preferred_date = _preferred_rate_date(date)
    rates = load_rate_records_for_date(preferred_date, currencies)
    actual_date = preferred_date

    if not rates:
        try:
            fetch_latest_rates(currencies=currencies, persist=True)
            rates, actual_date = load_latest_rate_records(currencies)
        except Exception:
            rates, actual_date = load_latest_rate_records(currencies)

    if actual_date is None:
        actual_date = preferred_date

    return rates, actual_date.strftime("%d.%m.%Y")


def get_nows_date():
    now = datetime.now()
    return now.strftime("%d.%m.%Y %H:%M:%S")


def get_currency_analytics_data(currencies: list, source: str = "nbu") -> dict:
    """Returns NBU rate history for the currency analytics charts."""
    if not currencies:
        return {"base_code": "UAH", "currencies": [], "rates": [], "latest_date": None}

    placeholders = ",".join(["?"] * len(currencies))
    query = f"""
        SELECT target_code, rate, date
        FROM exchange_rates
        WHERE source = ? AND target_code IN ({placeholders})
        ORDER BY target_code
    """

    points = []
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute(query, [source] + currencies)

        for row in cur.fetchall():
            parsed_date = parse_rate_date(row["date"])
            if parsed_date is None:
                continue

            points.append(
                {
                    "code": row["target_code"],
                    "date": parsed_date.isoformat(),
                    "label": parsed_date.strftime("%d.%m"),
                    "rate": float(row["rate"]),
                }
            )

    points.sort(key=lambda item: (item["date"], item["code"]))
    available_codes = [code for code in currencies if any(point["code"] == code for point in points)]
    latest_date = max((point["date"] for point in points), default=None)

    return {
        "base_code": "UAH",
        "currencies": available_codes,
        "rates": points,
        "latest_date": latest_date,
    }
