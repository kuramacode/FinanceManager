import datetime
from flask_login import current_user
from flask import abort, request
import sqlite3
import sys 
import os

from app.utils.database import sqlite_db_path


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def get_userid(): # Функція для отримання ID поточного користувача (якщо він аутентифікований) або None (якщо користувач не аутентифікований) 
    """Повертає ID поточного авторизованого користувача."""
    if current_user and current_user.is_authenticated: # Перевіряє, чи є поточний користувач та чи він аутентифікований
        return current_user.id # Повертає ID поточного користувача, якщо він аутентифікований
    return abort(403) # Повертає 403, якщо користувач не аутентифікований або відсутній

def get_username():
    """Повертає ім’я поточного авторизованого користувача."""
    return current_user.username

def _db_path() -> str: 
    """Повертає шлях до поточної SQLite-бази даних."""
    return sqlite_db_path()

def get_categories_lookup(userId):
    """Повертає дані у функції `get_categories_lookup`."""
    categories = get_categories(userId) # Отримання списку категорій для конкретного користувача
    return { # Створення словника, де ключами є ID категорій, а значеннями є словники з назвою та емодзі категорії
        category['id']: {  # Використання ID категорії як ключа словника
            'name': category['name'], # Використання назви категорії як значення для ключа 'name' у внутрішньому словнику
            'emoji': category['emoji'], # Використання емодзі категорії як значення для ключа 'emoji' у внутрішньому словнику
        }
        for category in categories # Ітерування по списку категорій, отриманих для конкретного користувача, для заповнення словника
    }

def get_transactions(userId):
    """Повертає дані у функції `get_transactions`."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()

        cur.execute('''SELECT * FROM transactions
                    WHERE user_id = ?
                    ORDER BY date DESC
                    ''' , (userId,))

        return cur.fetchall()

def get_categories(userId):
    """Повертає дані у функції `get_categories`."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute('''SELECT * FROM categories WHERE user_id = ?''', (userId,))
        return cur.fetchall()


def get_last_transactions(userId):
    """Повертає дані у функції `get_last_transactions`."""
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


def get_sum_income(userId):
    """Повертає дані у функції `get_sum_income`."""
    with sqlite3.connect(_db_path()) as database: 
        cur = database.cursor()
        cur.execute( # Виконання SQL-запиту для отримання суми доходів (типу 'income') для конкретного користувача, використовуючи COALESCE для обробки випадків, коли сума може бути NULL
            '''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?''',
            (userId, 'income'),
        )
        return abs(cur.fetchone()[0]) # Повертає абсолютне значення суми доходів, отриманої з бази даних, щоб забезпечити позитивне значення навіть якщо сума була від'ємною (хоча для доходів це не повинно бути так)


def get_sum_expense(userId):
    """Повертає дані у функції `get_sum_expense`."""
    with sqlite3.connect(_db_path()) as database:
        cur = database.cursor()
        cur.execute(
            '''SELECT COALESCE(SUM(amount), 0) FROM transactions
               WHERE user_id = ? AND type = ?''',
            (userId, 'expense'),
        )
        return abs(cur.fetchone()[0])


def filter_transactions(user_id, type):
    """Виконує логіку функції `filter_transactions`."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()

        if type == 'all':
            cur.execute(
                '''SELECT * FROM transactions
                   WHERE user_id = ?
                   ORDER BY date DESC''',
                (user_id,),
            )
        else:
            cur.execute(
                '''SELECT * FROM transactions
                   WHERE user_id = ? AND type = ?
                   ORDER BY date DESC''',
                (user_id, type),
            )

        return cur.fetchall()


def add_transaction(user_id, amount, date, description, category_id, type):
    """Додає дані у функції `add_transaction`."""
    with sqlite3.connect(_db_path()) as database:
        cur = database.cursor()
        cur.execute(
            '''INSERT INTO transactions(amount, date, description, user_id, category_id, type)
               VALUES(?, ?, ?, ?, ?, ?)''',
            (amount, date, description, user_id, category_id, type),
        )
        database.commit()


def get_data_for_register(): # отримуєм данні для реєстрації
    """Повертає дані у функції `get_data_for_register`."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password_repeat = request.form.get('password_repeat')
    
    return username, email, password, password_repeat

def get_data_for_login(): # отримуєм данні для входу
    """Повертає дані у функції `get_data_for_login`."""
    username = request.form.get('username')
    password = request.form.get('password')

    return username, password

def get_data_for_tx(): # отримуєм данні для додавання транзакцій
    """Зчитує дані форми для створення транзакції."""
    amount = request.form.get('f_amount')
    name = request.form.get('f_name')
    date = request.form.get('f_date')
    time = request.form.get('f_time')
    category = request.form.get('f_category')
    type = request.form.get('f_type')

    return amount, name, date, time, category, type

def normalized_date(date: str, time: str):
    """Об’єднує дату та час в об’єкт datetime."""
    from app.utils.formatting import format_date_for_DB
    year, month, day = format_date_for_DB(date)
    hours, minutes = format_time(time)
    normalized_date = datetime.datetime(year, month, day, hours, minutes, 0)

    return normalized_date




def format_time(time: str):
    """Форматує дані у функції `format_time`."""
    if not time or time == "None":
        hours, minutes = 0, 0
        return hours, minutes
    hours, minutes = time.split(':')

    return int(hours), int(minutes)
