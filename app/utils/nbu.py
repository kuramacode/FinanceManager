import sqlite3
import requests
from datetime import datetime
from app.config import Config
from app.utils.database import sqlite_db_path


FORMAT = "%d.%m.%Y"
f_date = datetime.now()
date = f_date.strftime("%Y%m%d")

base_code = 'UAH'
source = 'nbu'

nbu_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 15, 30)
if nbu_time > f_date:
    pass
else:
    url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date={date}&json"

    response = requests.get(url)
    data = response.json()

    db = sqlite3.connect(sqlite_db_path())
    cur = db.cursor()

    for item in data:
        target_code, rate, date = item.get('cc'), item.get('rate'), item.get('exchangedate')
        cur.execute('''INSERT INTO exchange_rates(base_code, target_code, rate, date, source) VALUES(?, ?, ?, ?, ?)''', (base_code, target_code, rate, date, source))
        db.commit()
    db.close()
