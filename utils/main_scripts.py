import datetime
from flask_login import current_user
from flask import abort, request
import sqlite3
import sys 
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def get_userid(): # Функція для отримання ID поточного користувача (якщо він аутентифікований) або None (якщо користувач не аутентифікований) 
    if current_user and current_user.is_authenticated: # Перевіряє, чи є поточний користувач та чи він аутентифікований
        return current_user.id # Повертає ID поточного користувача, якщо він аутентифікований
    return abort(403) # Повертає 403, якщо користувач не аутентифікований або відсутній

def get_username():
    return current_user.username

def get_transactions(userId):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()

    cur.execute('''SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                ''' , (userId,))

    transactions = cur.fetchall()
    database.close()

    return transactions

def get_categories(userId):
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    cur.execute('''SELECT * FROM categories WHERE user_id = ?''', (userId,))

    categories = cur.fetchall()
    db.close()

    return categories

def get_last_transactions(userId):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()

    cur.execute('''SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY date DESC
                LIMIT 5
                ''', (userId,))
    transactions = cur.fetchall()
    database.close()

    return transactions

def get_sum_income(userId):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()
    type = 'income'

    cur.execute('''SELECT * FROM transactions WHERE user_id = ?''', (userId,))
    list = cur.fetchall()
    if len(list) > 0:
        cur.execute('''SELECT SUM(amount) FROM transactions
                    WHERE user_id = ? AND type = ?''', (userId, type,))
        sum = cur.fetchall()

        return abs(sum[0][0])
    return 0

def get_sum_expense(userId):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()
    type = 'expense'

    cur.execute('''SELECT * FROM transactions WHERE user_id = ?
                ORDER BY date DESC''', (userId,))
    list = cur.fetchall()
    if len(list) > 0:
        cur.execute('''SELECT SUM(amount) FROM transactions
                    WHERE user_id = ? AND type = ?
                    ORDER BY date DESC''', (userId, type,))
        sum = cur.fetchall()
        return abs(sum[0][0])
    return 0

def filter_transactions(user_id, type):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()

    if type == 'all':
        cur.execute('''SELECT * FROM transactions WHERE user_id=?''', (user_id,))
        filtered = cur.fetchall()
    else:
        cur.execute('''SELECT * FROM transactions
                    WHERE user_id = ? AND type = ?''', (user_id, type,))
        filtered = cur.fetchall()
    database.close()

    return filtered

def add_transaction(user_id, amount, date, description, category_id, type):
    database = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')) # Підключення до бази даних SQLite за допомогою шляху, визначеного в конфігурації
    database.row_factory = sqlite3.Row
    cur = database.cursor()

    cur.execute('''INSERT INTO transactions(amount, date, description, user_id, category_id, type)
                VALUES(?, ?, ?, ?, ?, ?)''', 
                (amount, date, description, user_id, category_id, type))
    
    database.commit()
    database.close()
    
    return "Success"

def get_data_for_register(): # отримуєм данні для реєстрації
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password_repeat = request.form.get('password_repeat')
    
    return username, email, password, password_repeat

def get_data_for_login(): # отримуєм данні для входу
    username = request.form.get('username')
    password = request.form.get('password')

    return username, password

def get_data_for_tx(): # отримуєм данні для додавання транзакцій
    amount = request.form.get('f_amount')
    name = request.form.get('f_name')
    date = request.form.get('f_date')
    time = request.form.get('f_time')
    category = request.form.get('f_category')
    type = request.form.get('f_type')

    return amount, name, date, time, category, type

def normalized_date(date: str, time: str):
    year, month, day = format_date_for_DB(date)
    hours, minutes = format_time(time)
    normalized_date = datetime.datetime(year, month, day, hours, minutes, 0)

    return normalized_date

def format_date_for_DB(date):

    year, month, day = date.split('-')

    return  int(year), int(month), int(day)


def format_time(time: str):
    if not time or time == "None":
        hours, minutes = 0, 0
        return hours, minutes
    hours, minutes = time.split(':')

    return int(hours), int(minutes)