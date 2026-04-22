from app.utils.consts import CURRENT_YEAR, MONTHS
from app.i18n import format_month as format_i18n_month
from app.utils.main_scripts import _db_path
from app.utils.formatting import format_day, format_month, format_time
import sqlite3
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # Тепер це спрацює!


def color_change(value) -> str:
    """Returns a presentation class for transaction types or numeric deltas."""
    if isinstance(value, (int, float)):
        if value > 0:
            return "pos"
        if value < 0:
            return "neg"
        return "neutral"

    normalized = str(value or "").strip().lower()
    if normalized == "income":
        return "pos"
    if normalized == "expense":
        return "neg"

    try:
        numeric_value = float(normalized)
    except (TypeError, ValueError):
        return "neutral"

    if numeric_value > 0:
        return "pos"
    if numeric_value < 0:
        return "neg"
    return "neutral"


def format_date_for_website(date: str) -> str:
    """Форматує дату для шаблонів сайту."""
    subdates = date.split(' ')
    date_part, time_part = subdates[0], subdates[1]

    year, month, day = date_part.split('-')
    day, month, time = format_day(day), format_i18n_month(month, short=True), format_time(time_part)
    if int(year) != CURRENT_YEAR:
        return f"{month} {day} {year} {time}"
    return f"{month} {day} {time}"


def category_name(category_id: int, user_id: int) -> str:
    """Повертає назву категорії за ідентифікатором."""
    db = sqlite3.connect(_db_path())
    cur = db.cursor()

    cur.execute('''SELECT name FROM categories WHERE user_id = ? AND id = ?''', (user_id, category_id))
    category_name = cur.fetchall()[0][0]

    return category_name


def category_emoji(category_id: int, user_id: int) -> str:
    """Повертає emoji категорії за ідентифікатором."""
    db = sqlite3.connect(_db_path())
    cur = db.cursor()

    cur.execute('''SELECT emoji FROM categories WHERE user_id = ? AND id = ?''', (user_id, category_id))
    category_emoji = cur.fetchall()[0][0]

    return category_emoji


def currency_flag(target_code: str) -> str:
    """Повертає прапор валюти за кодом."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()

        cur.execute('''SELECT flag FROM currencies WHERE code=?''', (target_code, ))

        flag_fetch = cur.fetchall()

        if len(flag_fetch) == 0:
            return '🇺🇳'
        return flag_fetch[0][0]


def get_difference_percentage(date: datetime, code: str):
    """Повертає відсоткову зміну курсу відносно попереднього дня."""
    if not date or not code:
        return 0

    if not isinstance(date, datetime):
        try:
            date = datetime.strptime(str(date), "%d.%m.%Y")
        except ValueError:
            return 0
    yesterday = date - timedelta(days=1)

    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()

        cur.execute('''SELECT rate FROM exchange_rates WHERE date=? AND target_code=?''', (date.strftime("%d.%m.%Y"), code,))
        today_row = cur.fetchone()

        cur.execute('''SELECT rate FROM exchange_rates WHERE date=? AND target_code=?''', (yesterday.strftime("%d.%m.%Y"), code,))
        yesterday_row = cur.fetchone()

        if not today_row or not yesterday_row or not yesterday_row[0]:
            return 0

        today_rate = today_row[0]
        yesterday_rate = yesterday_row[0]

        difference_percentage = ((today_rate - yesterday_rate) / yesterday_rate) * 100

        return difference_percentage


def get_difference(date):
    """Повертає різницю курсів між поточним і попереднім днем."""
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
