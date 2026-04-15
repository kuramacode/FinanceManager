from app.utils.main_scripts import _db_path
import sqlite3

def get_income_categories(user_id):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        built_in = cur.execute('''SELECT * FROM categories WHERE built_in="True" AND type="income"''').fetchall()
        users = cur.execute('''SELECT * FROM categories WHERE user_id=? AND type="income"''', (user_id,)).fetchall()

    return built_in + users

def get_expense_categories(user_id):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        built_in = cur.execute('''SELECT * FROM categories WHERE built_in="False" AND type="expense"''').fetchall()
        users = cur.execute('''SELECT * FROM categories WHERE user_id=? AND type="expense"''', (user_id,)).fetchall()

    return built_in + users