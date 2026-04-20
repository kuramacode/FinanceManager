from flask import request

def get_data_for_tx(): # отримуєм данні для додавання транзакцій
    """Повертає дані у функції `get_data_for_tx`."""
    amount = request.form.get('f_amount')
    name = request.form.get('f_name')
    date = request.form.get('f_date')
    time = request.form.get('f_time')
    category = request.form.get('f_category')
    type = request.form.get('f_type')

    return amount, name, date, time, category, type

def normalized_date(date: str, time: str):
    """Виконує логіку функції `normalized_date`."""
    from app.utils.formatting import format_time, format_date_for_DB
    year, month, day = format_date_for_DB(date)
    hours, minutes = format_time(time)
    import datetime
    normalized_date = datetime.datetime(year, month, day, hours, minutes, 0)

    return normalized_date
