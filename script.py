import sqlite3

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


db = sqlite3.connect('instance/users.db')
cur = db.cursor()



create_table_users()
create_table_transactions()

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

for i in range(len(transactions)):
    amount, date, description, user_id, category_id, type = transactions[i].values()
    insert_transaction(amount, date, description, user_id, category_id, type)
cur.execute('SELECT * FROM users')
print(cur.fetchall())
cur.execute('SELECT * FROM transactions')
print(cur.fetchall())