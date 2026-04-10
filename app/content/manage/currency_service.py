import sqlite3
from app.utils.main_scripts import _db_path
from datetime import datetime, timedelta

def get_rates(date: str):
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        nbu_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 15, 30)
        date_time = datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
        
        if nbu_time > date_time:
            yesterday = datetime.now() - timedelta(days=1)
            date = yesterday.strftime("%d.%m.%Y")
            
            cur.execute(''' SELECT * FROM exchange_rates
                    WHERE date=? ''',
                    (date,))
        else:
            date = date_time.strftime("%d.%m.%Y")
            cur.execute(''' SELECT * FROM exchange_rates
                    WHERE date=? ''',
                    (date,))
        
        return cur.fetchall(), date
    
def get_nows_date():
    now = datetime.now()
    return now.strftime("%d.%m.%Y %H:%M:%S")

