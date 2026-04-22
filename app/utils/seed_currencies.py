from __future__ import annotations

import sqlite3

from app.utils.database import ensure_sqlite_directory, sqlite_db_path


CURRENCIES = [
    {"id": 1, "code": "USD", "name": "US Dollar", "flag": "🇺🇸"},
    {"id": 2, "code": "EUR", "name": "Euro", "flag": "🇪🇺"},
    {"id": 3, "code": "GBP", "name": "British Pound", "flag": "🇬🇧"},
    {"id": 4, "code": "CHF", "name": "Swiss Franc", "flag": "🇨🇭"},
    {"id": 5, "code": "JPY", "name": "Japanese Yen", "flag": "🇯🇵"},
    {"id": 6, "code": "CNY", "name": "Chinese Yuan", "flag": "🇨🇳"},
    {"id": 7, "code": "KRW", "name": "South Korean Won", "flag": "🇰🇷"},
    {"id": 8, "code": "PLN", "name": "Polish Zloty", "flag": "🇵🇱"},
    {"id": 9, "code": "CZK", "name": "Czech Koruna", "flag": "🇨🇿"},
    {"id": 10, "code": "HUF", "name": "Hungarian Forint", "flag": "🇭🇺"},
    {"id": 11, "code": "NOK", "name": "Norwegian Krone", "flag": "🇳🇴"},
    {"id": 12, "code": "SEK", "name": "Swedish Krona", "flag": "🇸🇪"},
    {"id": 13, "code": "CAD", "name": "Canadian Dollar", "flag": "🇨🇦"},
    {"id": 14, "code": "BRL", "name": "Brazilian Real", "flag": "🇧🇷"},
    {"id": 15, "code": "TRY", "name": "Turkish Lira", "flag": "🇹🇷"},
    {"id": 16, "code": "AED", "name": "UAE Dirham", "flag": "🇦🇪"},
]


def seed_currencies() -> int:
    ensure_sqlite_directory()

    query = """
        INSERT INTO currencies (id, code, name, flag)
        VALUES (:id, :code, :name, :flag)
        ON CONFLICT(id) DO UPDATE SET
            code = excluded.code,
            name = excluded.name,
            flag = excluded.flag
    """

    with sqlite3.connect(sqlite_db_path()) as database:
        database.executemany(query, CURRENCIES)
        database.commit()

    return len(CURRENCIES)


def main() -> None:
    count = seed_currencies()
    print(f"Seeded currencies: {count}")


if __name__ == "__main__":
    main()
