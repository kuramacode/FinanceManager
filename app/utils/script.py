import sqlite3
import sys 
import os
from datetime import datetime, time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def create_table_users():
    """Створює дані у функції `create_table_users`."""
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, password TEXT)''')
    db.commit()
    db.close()
    return "Table created successfully"

def create_table_transactions():
    """Створює дані у функції `create_table_transactions`."""
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY, amount FLOAT, date DATETIME,
                 description TEXT, user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))''')
    db.commit()
    db.close()
    return "Table created successfully"

def create_table_categories():
    """Створює дані у функції `create_table_categories`."""
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY, name TEXT,
                user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))''')
    
db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
cur = db.cursor()

create_table_categories()


def insert_transaction(amount, date, description, user_id, category_id, type):
    """Додає дані у функції `insert_transaction`."""
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''INSERT INTO transactions(amount, date, description, user_id, category_id, type) VALUES(?, ?, ?, ?, ?, ?)''', (amount, date, description, user_id, category_id, type))
    db.commit()
    db.close()
    return "Transaction inserted successfully"
def insert_user(username, email, password):
    """Додає дані у функції `insert_user`."""
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''INSERT INTO users(username, email, password) VALUES(?, ?, ?)''', (username, email, password))
    db.commit()
    db.close()
    return "User inserted successfully"

def insert_categories(name, userId, desc, emoji, built_in, type):
    """Додає дані у функції `insert_categories`."""
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()
    cur.execute('''INSERT INTO categories(name, user_id, desc, emoji, built_in, type) VALUES(?, ?, ?, ?, ?, ?)''', (name, userId, desc, emoji, built_in, type))
    db.commit()
    db.close()
    return "Success"

def get_categories(user_id):
    """Повертає дані у функції `get_categories`."""
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''SELECT * FROM categories WHERE user_id = ?''', (user_id))

    categories = cur.fetchall()

    return categories

db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
db.row_factory = sqlite3.Row
cur = db.cursor()

users = [
    {"username": 'Alex', "email": 'takase00143@1smail.top', 'password': 'password123' },
    {"username": 'Tina', "email": 'nps5avesktk@duxer.top', 'password': 'password456' },
    {"username": 'Max', "email": 'predj@gtgstoreid.com', 'password': 'password789' },
]

transactions = [
    {"amount": 2500.00, "date": "2026-03-01 09:00:00", "description": "Salary payment", "user_id": 5, "category_id": 1, "type": "income"},
    {"amount": -150.75, "date": "2026-03-02 13:20:00", "description": "Grocery shopping", "user_id": 5, "category_id": 2, "type": "expense"},
    {"amount": -80.00, "date": "2026-03-03 18:30:00", "description": "Cinema ticket", "user_id": 5, "category_id": 3, "type": "expense"},
    {"amount": -300.00, "date": "   ", "description": "Restaurant dinner", "user_id": 5, "category_id": 4, "type": "expense"},
    {"amount": 500.00, "date": "2026-03-05 10:00:00", "description": "Freelance project", "user_id": 5, "category_id": 1, "type": "income"},
]

categor = [
    {"name": "Food", "user_id": 5},
    {"name": "Transport", "user_id": 5},
    {"name": "Entertainment", "user_id": 5},
    {"name": "Health", "user_id": 5},
    {"name": "Shopping", "user_id": 5},
    {"name": "Bills", "user_id": 5},
    {"name": "Other", "user_id": 5}
]

categorie = {
    1: "Salary / Freelance",    # income-type activities
    2: "Groceries / Doctor",    # food and health
    3: "Entertainment",         # cinema tickets
    4: "Dining / Coffee",       # restaurant & coffee
    5: "Education",             # online courses
    6: "Electronics",           # gadgets purchase
    7: "Books"                  # books
}

categories = [
    {
        "name": "Clothing",
        "user_id": "3",
        "desc": "Clothes, shoes, and accessories",
        "emoji": "👕",
        "type": "expense",
        "built_in": "False"
    },
    {
        "name": "Fuel",
        "user_id": "3",
        "desc": "Gasoline or diesel for vehicles",
        "emoji": "⛽",
        "type": "expense",
        "built_in": "False"
    },
    {
        "name": "Fast Food",
        "user_id": "3",
        "desc": "Quick meals, street food, takeaways",
        "emoji": "🍔",
        "type": "expense",
        "built_in": "False"
    },
    {
        "name": "Coffee",
        "user_id": "3",
        "desc": "Coffee shops and drinks",
        "emoji": "☕",
        "type": "expense",
        "built_in": "False"
    },
    {
        "name": "Taxi",
        "user_id": "3",
        "desc": "Ride services and taxis",
        "emoji": "🚕",
        "type": "expense",
        "built_in": "False"
    },
    {
        "name": "Gaming",
        "user_id": "3",
        "desc": "Games, in-game purchases, platforms",
        "emoji": "🎮",
        "type": "expense",
        "built_in": "False"
    }
]

CURRENCIES = [
  { "code": 'USD', "name": 'US Dollar', "flag": "🇺🇸"      },
  { "code": 'EUR', "name": 'Euro', "flag": "🇪🇺"             },
  { "code": 'GBP', "name": 'British Pound', "flag": "🇬🇧"    },
  { "code": 'CHF', "name": 'Swiss Franc', "flag": "🇨🇭"      },
  { "code": 'JPY', "name": 'Japanese Yen', "flag": "🇯🇵"     },
  { "code": 'CNY', "name": 'Chinese Yuan', "flag": "🇨🇳"    },
  { "code": 'KRW', "name": 'South Korean Won', "flag": "🇰🇷" },
  { "code": 'PLN', "name": 'Polish Złoty', "flag": "🇵🇱"     },
  { "code": 'CZK', "name": 'Czech Koruna', "flag": "🇨🇿"     },
  { "code": 'HUF', "name": 'Hungarian Forint', "flag": "🇭🇺" },
  { "code": 'NOK', "name": 'Norwegian Krone', "flag": "🇳🇴"  },
  { "code": 'SEK', "name": 'Swedish Krona', "flag": "🇸🇪"    },
  { "code": 'CAD', "name": 'Canadian Dollar', "flag": "🇨🇦"  },
  { "code": 'BRL', "name": 'Brazilian Real', "flag": "🇧🇷"   },
  { "code": 'TRY', "name": 'Turkish Lira', "flag": "🇹🇷"     },
  { "code": 'AED', "name": 'UAE Dirham', "flag": "🇦🇪"     },
];
currencies = ['AED', 'BRL',
             'CAD', 'CHF',
             'CNY', 'CZK',
             'EUR', 'GBP',
             'HUF', 'JPY',
             'KRW', 'NOK',
             'PLN', 'SEK',
             'TRY', 'USD']



"""import requests

url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date=20260411&json"
base_code = 'UAH'
source = 'nbu'
response = requests.get(url)
data = response.json()

db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
cur = db.cursor()

for item in data:
    target_code, rate, date = item.get('cc'), item.get('rate'), item.get('exchangedate')
    cur.execute('''INSERT INTO exchange_rates(base_code, target_code, rate, date, source) VALUES(?, ?, ?, ?, ?)''', (base_code, target_code, rate, date, source))
    db.commit()
db.close()"""
db.row_factory = sqlite3.Row
useri = cur.execute('''
                    SELECT id FROM users
                    ''').fetchall()
ids = []

for user in useri:
    for item in user:
        ids.append(item)
    
    
print(ids)
