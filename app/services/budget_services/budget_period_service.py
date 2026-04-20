from datetime import date, datetime, timedelta


def _coerce_date(value):
    """Приводить значення до потрібного типу у функції `_coerce_date`."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError(f"Unsupported date value: {value!r}")


def _today():
    """Виконує логіку функції `_today`."""
    return date.today()


def get_current_period(budget):
    """Повертає дані у функції `get_current_period`."""
    today = _today()

    start_date = _coerce_date(budget.get("start_date"))
    end_date = _coerce_date(budget.get("end_date"))
    period_type = budget.get("period_type")

    if start_date and today < start_date:
        return None

    if period_type == "custom":
        if end_date and today > end_date:
            return None
        return start_date, end_date

    if period_type == "monthly":
        start = date(today.year, today.month, 1)

        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        return start, end

    if period_type == "weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)

        return start, end

    return start_date, end_date
