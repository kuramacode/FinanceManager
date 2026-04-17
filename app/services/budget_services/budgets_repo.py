import sqlite3
from datetime import date, datetime
from app.utils.main_scripts import _db_path


def _parse_db_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def _normalize_budget_row(row):
    budget = dict(row)
    budget["start_date"] = _parse_db_date(budget.get("start_date"))
    budget["end_date"] = _parse_db_date(budget.get("end_date"))
    budget["amount_limit"] = float(budget.get("amount_limit") or 0.0)
    budget["currency_code"] = (budget.get("currency_code") or "UAH").upper()
    budget["period_type"] = (budget.get("period_type") or "custom").lower()
    return budget


def _normalize_category_row(row):
    category = dict(row)
    category["built_in"] = str(category.get("built_in", "")).strip().lower() in {"1", "true"}
    return category


def get_user_budgets(user_id):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        rows = cur.execute(
            '''
            SELECT id, name, desc, amount_limit, currency_code, period_type, start_date, end_date
            FROM budgets
            WHERE user_id=?
            ORDER BY start_date DESC, id DESC
            ''',
            (user_id,),
        ).fetchall()

        return [_normalize_budget_row(row) for row in rows]


def get_budget_by_id(budget_id: int, user_id: int):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        row = cur.execute(
            '''
            SELECT id, name, desc, amount_limit, currency_code, period_type, start_date, end_date
            FROM budgets
            WHERE id=? AND user_id=?
            ''',
            (budget_id, user_id),
        ).fetchone()

        if row is None:
            return None

        return _normalize_budget_row(row)


def get_budget_category_ids(budget_id: int) -> list[int]:
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        rows = cur.execute(
            '''
            SELECT category_id FROM budget_categories
            WHERE budget_id=?
            ''',
            (budget_id,),
        ).fetchall()

        return [row["category_id"] for row in rows]


def get_budget_category_ids_map(budget_ids: list[int]) -> dict[int, list[int]]:
    if not budget_ids:
        return {}

    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        placeholders = ",".join("?" for _ in budget_ids)
        rows = cur.execute(
            f'''
            SELECT budget_id, category_id
            FROM budget_categories
            WHERE budget_id IN ({placeholders})
            ORDER BY budget_id, category_id
            ''',
            budget_ids,
        ).fetchall()

    category_map = {budget_id: [] for budget_id in budget_ids}
    for row in rows:
        category_map.setdefault(row["budget_id"], []).append(row["category_id"])

    return category_map


def get_budget_categories_map(budget_ids: list[int]) -> dict[int, list[dict]]:
    if not budget_ids:
        return {}

    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        placeholders = ",".join("?" for _ in budget_ids)
        rows = cur.execute(
            f'''
            SELECT bc.budget_id, c.id, c.name, c.desc, c.emoji, c.type, c.built_in
            FROM budget_categories AS bc
            JOIN categories AS c ON c.id = bc.category_id
            WHERE bc.budget_id IN ({placeholders})
            ORDER BY bc.budget_id, c.name
            ''',
            budget_ids,
        ).fetchall()

    category_map = {budget_id: [] for budget_id in budget_ids}
    for row in rows:
        category = _normalize_category_row(row)
        budget_id = category.pop("budget_id")
        category_map.setdefault(budget_id, []).append(category)

    return category_map


def get_budgetable_categories_by_ids(user_id: int, category_ids: list[int]) -> list[dict]:
    if not category_ids:
        return []

    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()

        placeholders = ",".join("?" for _ in category_ids)
        rows = cur.execute(
            f'''
            SELECT id, name, desc, emoji, type, built_in, user_id
            FROM categories
            WHERE id IN ({placeholders})
              AND type='expense'
              AND (
                  user_id=?
                  OR CAST(COALESCE(built_in, 0) AS TEXT) IN ('1', 'True', 'true')
              )
            ORDER BY name
            ''',
            [*category_ids, user_id],
        ).fetchall()

    return [_normalize_category_row(row) for row in rows]


def create_budget(user_id, name, desc, amount_limit, currency_code, period_type, start_date, end_date, category_ids):
    with sqlite3.connect(_db_path()) as db:
        cur = db.cursor()

        cur.execute(
            '''
            INSERT INTO budgets (user_id, name, desc, amount_limit, currency_code, period_type, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                name,
                desc,
                amount_limit,
                currency_code,
                period_type,
                start_date.isoformat(),
                end_date.isoformat(),
            ),
        )
        budget_id = cur.lastrowid

        if category_ids:
            cur.executemany(
                '''
                INSERT INTO budget_categories (budget_id, category_id)
                VALUES (?, ?)
                ''',
                [(budget_id, category_id) for category_id in category_ids],
            )

        db.commit()

    return get_budget_by_id(budget_id, user_id)


def update_budget(budget_id, user_id, name, desc, amount_limit, currency_code, period_type, start_date, end_date, category_ids):
    with sqlite3.connect(_db_path()) as db:
        cur = db.cursor()

        existing = cur.execute(
            '''
            SELECT id FROM budgets
            WHERE id=? AND user_id=?
            ''',
            (budget_id, user_id),
        ).fetchone()

        if existing is None:
            return None

        cur.execute(
            '''
            UPDATE budgets
            SET name=?, desc=?, amount_limit=?, currency_code=?, period_type=?, start_date=?, end_date=?
            WHERE id=? AND user_id=?
            ''',
            (
                name,
                desc,
                amount_limit,
                currency_code,
                period_type,
                start_date.isoformat(),
                end_date.isoformat(),
                budget_id,
                user_id,
            ),
        )

        cur.execute(
            '''
            DELETE FROM budget_categories
            WHERE budget_id=?
            ''',
            (budget_id,),
        )

        if category_ids:
            cur.executemany(
                '''
                INSERT INTO budget_categories (budget_id, category_id)
                VALUES (?, ?)
                ''',
                [(budget_id, category_id) for category_id in category_ids],
            )

        db.commit()

    return get_budget_by_id(budget_id, user_id)


def delete_budget(budget_id: int, user_id: int) -> bool:
    with sqlite3.connect(_db_path()) as db:
        cur = db.cursor()

        existing = cur.execute(
            '''
            SELECT id
            FROM budgets
            WHERE id=? AND user_id=?
            ''',
            (budget_id, user_id),
        ).fetchone()

        if existing is None:
            return False

        cur.execute(
            '''
            DELETE FROM budget_categories
            WHERE budget_id=?
            ''',
            (budget_id,),
        )

        result = cur.execute(
            '''
            DELETE FROM budgets
            WHERE id=?
            ''',
            (budget_id,),
        )
        db.commit()

    return result.rowcount > 0
