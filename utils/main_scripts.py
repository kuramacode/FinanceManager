
from flask_login import current_user
from flask import abort
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

    cur.execute('''SELECT * FROM transactions WHERE user_id = ?''', (userId,))
    list = cur.fetchall()
    if len(list) > 0:
        cur.execute('''SELECT SUM(amount) FROM transactions
                    WHERE user_id = ? AND type = ?''', (userId, type,))
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
