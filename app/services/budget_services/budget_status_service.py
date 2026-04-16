import sqlite3 
from app.utils.main_scripts import _db_path

def resolve(usage):
    with sqlite3.connect(_db_path()) as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor()
        
        