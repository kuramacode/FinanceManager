from app.utils.main_scripts import _db_path
import sqlite3

def get_sum_for_budget(user_id, categories, date_from, date_to):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        query = '''
        SELECT amount
        '''
        