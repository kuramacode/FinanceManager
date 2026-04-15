from app.utils.consts import CURRENT_YEAR, MONTHS
from app.utils.main_scripts import _db_path
from app.utils.formatting import format_day, format_month, format_time
import sqlite3
import sys 
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def color_change(type: str) -> str:
    if type.lower() == "income":
        return "pos"
    elif type.lower() == "expense":
        return "neg"
    else:
        return "neutral"

def format_date_for_website(date: str) -> str:
    subdates = date.split(' ')
    date_part, time_part = subdates[0], subdates[1]

    year, month, day = date_part.split('-')
    day, month, time = format_day(day), format_month(month), format_time(time_part)
    if int(year) != CURRENT_YEAR:
        return f"{month} {day} {year} {time}"
    return f"{month} {day} {time}"



def category_name(category_id: int, user_id: int) -> str:
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''SELECT name FROM categories WHERE user_id = ? AND id = ?''', (user_id, category_id))
    category_name = cur.fetchall()[0][0]

    return category_name

def category_emoji(category_id: int, user_id: int) -> str:
    db = sqlite3.connect(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
    cur = db.cursor()

    cur.execute('''SELECT emoji FROM categories WHERE user_id = ? AND id = ?''', (user_id, category_id))
    category_emoji = cur.fetchall()[0][0]

    return category_emoji

def currency_flag(target_code: str) -> str:
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()

        cur.execute('''SELECT flag FROM currencies WHERE code=?''', (target_code, ))
        
        flag_fetch = cur.fetchall()
        
        if len(flag_fetch) == 0:
            return '🇺🇳'
        else:
            return flag_fetch[0][0]
        
def get_difference_percentage(date: datetime, code: str):
    date = datetime.strptime(date, "%d.%m.%Y")
    yesterday = date - timedelta(days=1)
    
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        
        cur.execute('''SELECT rate FROM exchange_rates WHERE date=? AND target_code=?''', (date.strftime("%d.%m.%Y"), code,))
        today_rate = cur.fetchall()[0][0]
        
        cur.execute('''SELECT rate FROM exchange_rates WHERE date=? AND target_code=?''', (yesterday.strftime("%d.%m.%Y"), code,))
        yesterday_rate = cur.fetchall()[0][0]
        
        difference_percentage = ((today_rate - yesterday_rate) / yesterday_rate) * 100
        
        return difference_percentage
def get_difference(date):
    date = datetime.strptime(date, "%d.%m.%Y")
    yesterday = date - timedelta(days=1)
    
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        
        cur.execute('''SELECT rate FROM exchange_rates WHERE date=?''', (date.strftime("%d.%m.%Y"), ))
        today_rate = cur.fetchall()
        
        cur.execute('''SELECT rate FROM exchange_rates WHERE date=?''', (yesterday.strftime("%d.%m.%Y"), ))
        yesterday_rate = cur.fetchall()
        
        difference = today_rate - yesterday_rate
        
        return difference