from app.utils.consts import MONTHS

def format_day(day):
    if day.startswith('0'):
        return day[1:]
    return day
def format_month(month):
    return MONTHS.get(month, month)
    return MONTHS[month]

def format_time(time):
    parts = time.split(':')
    if len(parts) >= 2:
        hours, minutes = parts[0], parts[1]
        return f"{hours}:{minutes}"
    return time