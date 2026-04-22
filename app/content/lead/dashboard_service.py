import sqlite3
import sys; import os

from app.utils.database import sqlite_db_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config  # Тепер це спрацює!

def _db_path() -> str: 
    """Повертає шлях до поточної SQLite-бази даних."""
    return sqlite_db_path()

def _period_clause(start=None, end=None) -> tuple[str, list]:
    clause = ""
    params = []
    if start is not None:
        clause += " AND date >= ?"
        params.append(start.strftime("%Y-%m-%d %H:%M:%S"))
    if end is not None:
        clause += " AND date < ?"
        params.append(end.strftime("%Y-%m-%d %H:%M:%S"))
    return clause, params


def get_sum_income(userId, start=None, end=None):
    """Повертає суму доходів користувача."""
    with sqlite3.connect(_db_path()) as database: 
        cur = database.cursor()
        period_clause, period_params = _period_clause(start, end)
        cur.execute( # Виконання SQL-запиту для отримання суми доходів (типу 'income') для конкретного користувача, використовуючи COALESCE для обробки випадків, коли сума може бути NULL
            f'''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?{period_clause}''',
            (userId, 'income', *period_params),
        )
        return abs(cur.fetchone()[0]) # Повертає абсолютне значення суми доходів, отриманої з бази даних, щоб забезпечити позитивне значення навіть якщо сума була від'ємною (хоча для доходів це не повинно бути так)


def get_sum_expense(userId, start=None, end=None):
    """Повертає суму витрат користувача."""
    with sqlite3.connect(_db_path()) as database:
        cur = database.cursor()
        period_clause, period_params = _period_clause(start, end)
        cur.execute(
            f'''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?{period_clause}''',
            (userId, 'expense', *period_params),
        )
        return abs(cur.fetchone()[0])

def get_last_transactions(userId, start=None, end=None):
    """Повертає останні транзакції користувача."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        period_clause, period_params = _period_clause(start, end)
        cur.execute(
            f'''SELECT * FROM transactions
               WHERE user_id = ?{period_clause}
               ORDER BY date DESC
               LIMIT 5''',
            (userId, *period_params),
        )
        return cur.fetchall()
    

