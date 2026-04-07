import sqlite3
import sys; import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config  # Тепер це спрацює!

def _db_path() -> str: 
    return Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')

def get_sum_income(userId):
    with sqlite3.connect(_db_path()) as database: 
        cur = database.cursor()
        cur.execute( # Виконання SQL-запиту для отримання суми доходів (типу 'income') для конкретного користувача, використовуючи COALESCE для обробки випадків, коли сума може бути NULL
            '''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?''',
            (userId, 'income'),
        )
        return abs(cur.fetchone()[0]) # Повертає абсолютне значення суми доходів, отриманої з бази даних, щоб забезпечити позитивне значення навіть якщо сума була від'ємною (хоча для доходів це не повинно бути так)


def get_sum_expense(userId):
    with sqlite3.connect(_db_path()) as database:
        cur = database.cursor()
        cur.execute(
            '''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?''',
            (userId, 'expense'),
        )
        return abs(cur.fetchone()[0])

def get_last_transactions(userId):
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute(
            '''SELECT * FROM transactions
               WHERE user_id = ?
               ORDER BY date DESC
               LIMIT 5''',
            (userId,),
        )
        return cur.fetchall()
    

