from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import date, datetime, timedelta
from typing import Iterable

import requests

from app.utils.database import ensure_sqlite_directory, sqlite_db_path


BASE_CODE = "UAH"
SOURCE = "nbu"
DATE_FORMAT = "%Y-%m-%d"
NBU_DATE_FORMAT = "%Y%m%d"
NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"


def _parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FORMAT).date()


def _date_range(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _load_currency_codes(database: sqlite3.Connection) -> set[str]:
    rows = database.execute("SELECT code FROM currencies ORDER BY id").fetchall()
    return {str(row[0]).upper() for row in rows}


def _fetch_nbu_rates(day: date) -> list[dict]:
    last_error: requests.RequestException | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                NBU_URL,
                params={"date": day.strftime(NBU_DATE_FORMAT), "json": ""},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
            if attempt == 3:
                break
            time.sleep(attempt * 2)

    raise RuntimeError(f"Failed to fetch NBU rates for {day.isoformat()}") from last_error


def seed_exchange_rates(start: date, end: date) -> dict[str, int]:
    if end < start:
        raise ValueError("End date must not be earlier than start date.")

    ensure_sqlite_directory()

    upsert_query = """
        INSERT INTO exchange_rates (base_code, target_code, rate, date, source)
        VALUES (:base_code, :target_code, :rate, :date, :source)
        ON CONFLICT(base_code, target_code, date, source) DO UPDATE SET
            rate = excluded.rate
    """

    inserted = 0
    skipped = 0

    with sqlite3.connect(sqlite_db_path()) as database:
        currency_codes = _load_currency_codes(database)

        for day in _date_range(start, end):
            rows = []
            for item in _fetch_nbu_rates(day):
                target_code = str(item.get("cc", "")).upper()
                if target_code not in currency_codes:
                    skipped += 1
                    continue

                rows.append(
                    {
                        "base_code": BASE_CODE,
                        "target_code": target_code,
                        "rate": item["rate"],
                        "date": item["exchangedate"],
                        "source": SOURCE,
                    }
                )

            database.executemany(upsert_query, rows)
            inserted += len(rows)

        database.commit()

    return {"upserted": inserted, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import NBU exchange rates for currencies in DB.")
    parser.add_argument("--start", default="2026-03-21", help="Start date, inclusive, YYYY-MM-DD.")
    parser.add_argument("--end", default="2026-04-21", help="End date, inclusive, YYYY-MM-DD.")
    args = parser.parse_args()

    summary = seed_exchange_rates(start=_parse_date(args.start), end=_parse_date(args.end))
    print(f"Upserted exchange rates: {summary['upserted']}")
    print(f"Skipped non-configured currency rates: {summary['skipped']}")


if __name__ == "__main__":
    main()
