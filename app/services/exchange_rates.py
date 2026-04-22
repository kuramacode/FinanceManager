from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Iterable

from app.clients.nbu_client import fetch_rate_rows
from app.utils.database import ensure_sqlite_directory, sqlite_db_path


BASE_CODE = "UAH"
SOURCE = "nbu"
DISPLAY_DATE_FORMAT = "%d.%m.%Y"
SUPPORTED_DATE_FORMATS = (DISPLAY_DATE_FORMAT, "%Y-%m-%d")


def normalize_currency_code(code: str | None) -> str:
    return str(code or "").strip().upper()


def normalize_currency_codes(currencies: Iterable[str] | None) -> list[str]:
    seen = set()
    normalized = []
    for code in currencies or []:
        clean_code = normalize_currency_code(code)
        if clean_code and clean_code not in seen:
            seen.add(clean_code)
            normalized.append(clean_code)
    return normalized


def parse_rate_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    raw_value = str(value or "").strip()
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(raw_value, fmt).date()
        except ValueError:
            continue
    return None


def format_rate_date(value) -> str:
    parsed = parse_rate_date(value)
    if parsed is None:
        parsed = date.today()
    return parsed.strftime(DISPLAY_DATE_FORMAT)


def _load_rate_records(
    currencies: Iterable[str] | None = None,
    source: str = SOURCE,
) -> list[dict]:
    currency_codes = normalize_currency_codes(currencies)
    params: list = [BASE_CODE, source]
    filters = ["base_code = ?", "source = ?"]

    if currency_codes:
        placeholders = ",".join("?" for _ in currency_codes)
        filters.append(f"target_code IN ({placeholders})")
        params.extend(currency_codes)

    query = f"""
        SELECT base_code, target_code, rate, date, source
        FROM exchange_rates
        WHERE {" AND ".join(filters)}
    """

    try:
        with sqlite3.connect(sqlite_db_path()) as database:
            database.row_factory = sqlite3.Row
            rows = database.execute(query, params).fetchall()
    except (sqlite3.Error, ValueError):
        return []

    records = []
    for row in rows:
        parsed_date = parse_rate_date(row["date"])
        if parsed_date is None:
            continue
        records.append(
            {
                "base_code": row["base_code"],
                "target_code": normalize_currency_code(row["target_code"]),
                "rate": float(row["rate"]),
                "date": parsed_date.strftime(DISPLAY_DATE_FORMAT),
                "source": row["source"],
                "_parsed_date": parsed_date,
            }
        )
    return records


def load_latest_rate_records(
    currencies: Iterable[str] | None = None,
    source: str = SOURCE,
) -> tuple[list[dict], date | None]:
    records = _load_rate_records(currencies=currencies, source=source)
    if not records:
        return [], None

    latest_date = max(record["_parsed_date"] for record in records)
    latest_records = [
        {key: value for key, value in record.items() if key != "_parsed_date"}
        for record in records
        if record["_parsed_date"] == latest_date
    ]
    latest_records.sort(key=lambda item: item["target_code"])
    return latest_records, latest_date


def load_latest_rates_from_db(
    currencies: Iterable[str] | None = None,
    source: str = SOURCE,
) -> tuple[dict[str, float], date | None]:
    records, latest_date = load_latest_rate_records(currencies=currencies, source=source)
    if not records:
        return {}, latest_date

    rates = {BASE_CODE: 1.0}
    rates.update({record["target_code"]: float(record["rate"]) for record in records})
    return rates, latest_date


def load_rate_records_for_date(
    target_date,
    currencies: Iterable[str] | None = None,
    source: str = SOURCE,
) -> list[dict]:
    parsed_target = parse_rate_date(target_date)
    if parsed_target is None:
        return []

    records = _load_rate_records(currencies=currencies, source=source)
    selected_records = [
        {key: value for key, value in record.items() if key != "_parsed_date"}
        for record in records
        if record["_parsed_date"] == parsed_target
    ]
    selected_records.sort(key=lambda item: item["target_code"])
    return selected_records


def upsert_rate_records(records: Iterable[dict]) -> None:
    prepared_records = []
    for record in records:
        target_code = normalize_currency_code(record.get("target_code"))
        rate = record.get("rate")
        if not target_code or rate is None:
            continue
        prepared_records.append(
            {
                "base_code": normalize_currency_code(record.get("base_code")) or BASE_CODE,
                "target_code": target_code,
                "rate": float(rate),
                "date": format_rate_date(record.get("date")),
                "source": str(record.get("source") or SOURCE),
            }
        )

    if not prepared_records:
        return

    ensure_sqlite_directory()
    query = """
        INSERT INTO exchange_rates (base_code, target_code, rate, date, source)
        VALUES (:base_code, :target_code, :rate, :date, :source)
        ON CONFLICT(base_code, target_code, date, source) DO UPDATE SET
            rate = excluded.rate
    """

    try:
        with sqlite3.connect(sqlite_db_path()) as database:
            database.executemany(query, prepared_records)
            database.commit()
    except sqlite3.Error:
        return


def fetch_latest_rates(
    currencies: Iterable[str] | None = None,
    persist: bool = True,
) -> tuple[dict[str, float], date | None]:
    currency_codes = set(normalize_currency_codes(currencies))
    records = []

    for item in fetch_rate_rows():
        target_code = normalize_currency_code(item.get("cc"))
        if not target_code or (currency_codes and target_code not in currency_codes):
            continue

        records.append(
            {
                "base_code": BASE_CODE,
                "target_code": target_code,
                "rate": float(item["rate"]),
                "date": format_rate_date(item.get("exchangedate")),
                "source": SOURCE,
            }
        )

    if persist:
        upsert_rate_records(records)

    rates = {BASE_CODE: 1.0}
    rates.update({record["target_code"]: float(record["rate"]) for record in records})
    latest_date = max((parse_rate_date(record["date"]) for record in records), default=None)
    return rates, latest_date


def get_latest_rates(currencies: Iterable[str] | None = None) -> dict[str, float]:
    rates, _ = load_latest_rates_from_db(currencies=currencies)
    if rates:
        return rates

    rates, _ = fetch_latest_rates(currencies=currencies, persist=True)
    return rates
