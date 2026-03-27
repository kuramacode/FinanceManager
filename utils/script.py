import sqlite3
import sys 
import os
import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def create_table_users():
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, password TEXT)''')
    db.commit()
    db.close()
    return "Table created successfully"

def create_table_transactions():
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY, amount FLOAT, date DATETIME,
                 description TEXT, user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))''')
    db.commit()
    db.close()
    return "Table created successfully"

def create_table_categories():
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY, name TEXT,
                user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id))''')
    
db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
cur = db.cursor()

create_table_categories()


def insert_transaction(amount, date, description, user_id, category_id, type):
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''INSERT INTO transactions(amount, date, description, user_id, category_id, type) VALUES(?, ?, ?, ?, ?, ?)''', (amount, date, description, user_id, category_id, type))
    db.commit()
    db.close()
    return "Transaction inserted successfully"
def insert_user(username, email, password):
    db = sqlite3.connect('instance/users.db')
    cur = db.cursor()
    cur.execute('''INSERT INTO users(username, email, password) VALUES(?, ?, ?)''', (username, email, password))
    db.commit()
    db.close()
    return "User inserted successfully"

def insert_categories(name, userId, emoji):
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()
    cur.execute('''INSERT INTO categories(name, user_id, emoji) VALUES(?, ?, ?)''', (name, userId, emoji))
    db.commit()
    db.close()
    return "Success"

def get_categories(user_id):
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''SELECT * FROM categories WHERE user_id = ?''', (user_id))

    categories = cur.fetchall()

    return categories

db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
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
    {"amount": -300.00, "date": "2026-03-04 20:15:00", "description": "Restaurant dinner", "user_id": 5, "category_id": 4, "type": "expense"},
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
    {"name": "Salary", "user_id": "5", "emoji": "💸"},
    {"name": "Groceries / Doctor", "user_id": "5", "emoji": "💊"},
    {"name": "Entertainment", "user_id": "5", "emoji": "🎉"},
    {"name": "Dining / Coffee", "user_id": "5", "emoji": "🍵"},
    {"name": "Education", "user_id": "5", "emoji": "🏫"},
    {"name": "Electronics", "user_id": "5", "emoji": "💻"},
    {"name": "Books", "user_id": "5", "emoji": "📖"},
]


date = '25-01-2001'
time = '15:32'



date_n = datetime.datetime("2026", "12", "11", "15", "30", "0")

print(date_n)

nasm = {
    categorie['id']: {
        
    }
}