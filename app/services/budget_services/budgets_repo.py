import sqlite3 
from app.utils.main_scripts import _db_path

def get_active_budgets(user_id):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        rows = cur.execute('''
                    SELECT * FROM budgets
                    WHERE user_id=? AND is_activ=?
                    ''', (user_id, "True")).fetchall()
        
        return rows
        