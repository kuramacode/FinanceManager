import sqlite3
import requests
import json
from app.config import Config


url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
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
db.close()