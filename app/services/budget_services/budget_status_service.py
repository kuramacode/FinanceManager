def get_budget_status(spent, limit_amount):
    if limit_amount <= 0:
        return "invalid"

    percent = (spent / limit_amount) * 100

    if percent > 100:
        return "exceeded"
    if percent >= 80:
        return "warning"
    return "on_track"
