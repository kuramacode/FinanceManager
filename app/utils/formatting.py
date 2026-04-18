from app.utils.consts import MONTHS

def format_day(day):
    """Форматує дані у функції `format_day`."""
    if day.startswith('0'):
        return day[1:]
    return day
def format_month(month):
    """Форматує дані у функції `format_month`."""
    return MONTHS.get(month, month)
    return MONTHS[month]

def format_time(time):
    """Форматує дані у функції `format_time`."""
    parts = time.split(':')
    if len(parts) >= 2:
        hours, minutes = parts[0], parts[1]
        return f"{hours}:{minutes}"
    return time

def format_date_for_DB(date):

    """Форматує дані у функції `format_date_for_DB`."""
    year, month, day = date.split('-')

    return int(year), int(month), int(day)
