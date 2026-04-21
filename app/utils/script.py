from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_SEED_FILE = Path(__file__).with_name("user_2_seed_data.json")
DEFAULT_USER_ID = 2


def _sqlite_db_path() -> str:
    raw_uri = (os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL") or "").strip()
    if not raw_uri:
        return str((PROJECT_ROOT / "instance" / "users.db").resolve())

    if raw_uri == "sqlite:///:memory:":
        raise RuntimeError("In-memory SQLite cannot be used by this seed script.")
    if not raw_uri.startswith("sqlite:///"):
        raise RuntimeError(f"Unsupported database URI for this seed script: {raw_uri!r}")

    raw_path = raw_uri.replace("sqlite:///", "", 1)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / "instance" / raw_path
    return str(db_path.resolve())


def _connect() -> sqlite3.Connection:
    db = sqlite3.connect(_sqlite_db_path())
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def _load_seed_data(seed_file: Path) -> dict:
    with seed_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def _ensure_user_exists(db: sqlite3.Connection, user_id: int) -> None:
    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise RuntimeError(
            f"User with id={user_id} does not exist. Create this user before importing seed data."
        )


def _upsert_categories(db: sqlite3.Connection, categories: list[dict]) -> int:
    query = """
        INSERT INTO categories (id, name, desc, user_id, emoji, built_in, type)
        VALUES (:id, :name, :desc, :user_id, :emoji, :built_in, :type)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            desc = excluded.desc,
            user_id = excluded.user_id,
            emoji = excluded.emoji,
            built_in = excluded.built_in,
            type = excluded.type
    """
    rows = [
        {
            **category,
            "built_in": int(bool(category.get("built_in", False))),
        }
        for category in categories
    ]
    db.executemany(query, rows)
    return len(rows)


def _upsert_accounts(db: sqlite3.Connection, accounts: list[dict]) -> int:
    query = """
        INSERT INTO accounts (
            id, name, balance, status, currency_code, emoji, type, subtitle, note, user_id
        )
        VALUES (
            :id, :name, :balance, :status, :currency_code, :emoji, :type, :subtitle, :note, :user_id
        )
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            balance = excluded.balance,
            status = excluded.status,
            currency_code = excluded.currency_code,
            emoji = excluded.emoji,
            type = excluded.type,
            subtitle = excluded.subtitle,
            note = excluded.note,
            user_id = excluded.user_id
    """
    db.executemany(query, accounts)
    return len(accounts)


def _upsert_budgets(db: sqlite3.Connection, budgets: list[dict]) -> int:
    query = """
        INSERT INTO budgets (
            id, user_id, name, desc, amount_limit, currency_code, period_type, start_date, end_date
        )
        VALUES (
            :id, :user_id, :name, :desc, :amount_limit, :currency_code, :period_type, :start_date, :end_date
        )
        ON CONFLICT(id) DO UPDATE SET
            user_id = excluded.user_id,
            name = excluded.name,
            desc = excluded.desc,
            amount_limit = excluded.amount_limit,
            currency_code = excluded.currency_code,
            period_type = excluded.period_type,
            start_date = excluded.start_date,
            end_date = excluded.end_date
    """
    db.executemany(query, budgets)
    return len(budgets)


def _upsert_budget_categories(db: sqlite3.Connection, budget_categories: list[dict]) -> int:
    query = """
        INSERT INTO budget_categories (id, budget_id, category_id)
        VALUES (:id, :budget_id, :category_id)
        ON CONFLICT(id) DO UPDATE SET
            budget_id = excluded.budget_id,
            category_id = excluded.category_id
    """
    db.executemany(query, budget_categories)
    return len(budget_categories)


def _upsert_transactions(db: sqlite3.Connection, transactions: list[dict]) -> int:
    query = """
        INSERT INTO transactions (
            id, amount, date, description, user_id, category_id, type, account_id, currency_code
        )
        VALUES (
            :id, :amount, :date, :description, :user_id, :category_id, :type, :account_id, :currency_code
        )
        ON CONFLICT(id) DO UPDATE SET
            amount = excluded.amount,
            date = excluded.date,
            description = excluded.description,
            user_id = excluded.user_id,
            category_id = excluded.category_id,
            type = excluded.type,
            account_id = excluded.account_id,
            currency_code = excluded.currency_code
    """
    db.executemany(query, transactions)
    return len(transactions)


def import_seed_data(seed_file: Path = DEFAULT_SEED_FILE, user_id: int = DEFAULT_USER_ID) -> dict:
    data = _load_seed_data(seed_file)

    with _connect() as db:
        _ensure_user_exists(db, user_id)

        summary = {
            "accounts": _upsert_accounts(db, data.get("accounts", [])),
            "categories": _upsert_categories(db, data.get("categories", [])),
            "budgets": _upsert_budgets(db, data.get("budgets", [])),
            "budget_categories": _upsert_budget_categories(db, data.get("budget_categories", [])),
            "transactions": _upsert_transactions(db, data.get("transactions", [])),
        }
        db.commit()

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import FinanceManager seed data from JSON.")
    parser.add_argument(
        "--file",
        default=str(DEFAULT_SEED_FILE),
        help="Path to seed JSON file. Defaults to app/utils/user_2_seed_data.json.",
    )
    parser.add_argument(
        "--user-id",
        type=int,
        default=DEFAULT_USER_ID,
        help="User id that must exist before import. Defaults to 2.",
    )
    args = parser.parse_args()

    seed_file = Path(args.file).resolve()
    summary = import_seed_data(seed_file=seed_file, user_id=args.user_id)

    print(f"Imported seed data from: {seed_file}")
    for table, count in summary.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
