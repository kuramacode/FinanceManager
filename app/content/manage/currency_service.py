import sqlite3
from app.utils.main_scripts import _db_path
from datetime import datetime, timedelta

def get_rates(date: str, currencies: list):
    """Повертає дані у функції `get_rates`."""
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        
        nbu_time = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 15, 30)
        date_time = datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
        
        placeholders = ",".join(["?"] * len(currencies))
        query = f'''SELECT * FROM exchange_rates
            WHERE date = ? AND target_code IN ({placeholders})
            '''
            
        if nbu_time > date_time:
            yesterday = datetime.now() - timedelta(days=1)
            date = yesterday.strftime("%d.%m.%Y")
            params = [date] + currencies
            
            cur.execute(query, params)
            
        else:
            date = date_time.strftime("%d.%m.%Y")
            params = [date] + currencies
            
            cur.execute(query, params)
        
        return cur.fetchall(), date
    
def get_nows_date():
    """Повертає дані у функції `get_nows_date`."""
    now = datetime.now()
    return now.strftime("%d.%m.%Y %H:%M:%S")


def get_currency_analytics_data(currencies: list, source: str = "nbu") -> dict:
    """Повертає історію курсів для графіків валютної аналітики."""
    if not currencies:
        return {"base_code": "UAH", "currencies": [], "rates": [], "latest_date": None}

    placeholders = ",".join(["?"] * len(currencies))
    query = f"""
        SELECT target_code, rate, date
        FROM exchange_rates
        WHERE source = ? AND target_code IN ({placeholders})
        ORDER BY target_code
    """

    points = []
    with sqlite3.connect(_db_path()) as database:
        database.row_factory = sqlite3.Row
        cur = database.cursor()
        cur.execute(query, [source] + currencies)

        for row in cur.fetchall():
            try:
                parsed_date = datetime.strptime(row["date"], "%d.%m.%Y").date()
            except (TypeError, ValueError):
                continue

            points.append(
                {
                    "code": row["target_code"],
                    "date": parsed_date.isoformat(),
                    "label": parsed_date.strftime("%d.%m"),
                    "rate": float(row["rate"]),
                }
            )

    points.sort(key=lambda item: (item["date"], item["code"]))
    available_codes = [code for code in currencies if any(point["code"] == code for point in points)]
    latest_date = max((point["date"] for point in points), default=None)

    return {
        "base_code": "UAH",
        "currencies": available_codes,
        "rates": points,
        "latest_date": latest_date,
    }

