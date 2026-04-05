from app.utils.consts import CURRENT_YEAR, MONTHS
from app.utils.formatting import format_day, format_month, format_time
import sqlite3
import sys 
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def color_change(value: int) -> str:
    if value > 0:
        return "pos"
    elif value < 0:
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