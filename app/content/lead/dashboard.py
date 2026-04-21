from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from app.content.lead.dashboard_service import get_last_transactions, get_sum_expense, get_sum_income
from app.services.accounts import AccountService
from app.services.budget_services.budgets import BudgetService
from app.utils.main_scripts import get_categories_lookup, get_userid, get_username

_dashboard = Blueprint("dashboard", __name__)

account_service = AccountService()
budget_service = BudgetService()


def _build_dashboard_insights(balance, income_sum, budgets, transactions):
    """Формує службові дані у функції `_build_dashboard_insights`."""
    insights = []

    if income_sum > 0:
        savings_rate = round((balance / income_sum) * 100)
        if balance >= 0:
            insights.append(
                {
                    "icon": "↑",
                    "title": "Income is covering spending",
                    "text": f"Your current net result is positive with an estimated savings rate of {savings_rate}%.",
                }
            )
        else:
            insights.append(
                {
                    "icon": "!",
                    "title": "Expenses are ahead of income",
                    "text": f"Your current net result is negative and the estimated savings rate is {savings_rate}%.",
                }
            )

    exceeded_budget = next((budget for budget in budgets if budget.get("status") == "exceeded"), None)
    if exceeded_budget is not None:
        insights.append(
            {
                "icon": "!",
                "title": f"{exceeded_budget['name']} is over budget",
                "text": (
                    f"Spent {exceeded_budget['spent']:.2f} {exceeded_budget['currency_code']} "
                    f"against a limit of {exceeded_budget['amount_limit']:.2f} {exceeded_budget['currency_code']}."
                ),
            }
        )
    else:
        warning_budget = next((budget for budget in budgets if budget.get("status") == "warning"), None)
        if warning_budget is not None:
            insights.append(
                {
                    "icon": "•",
                    "title": f"{warning_budget['name']} is close to the limit",
                    "text": f"{warning_budget['percent']:.0f}% of that budget has already been used in the active period.",
                }
            )

    expense_transactions = [tx for tx in transactions if (tx["type"] or "").lower() == "expense"]
    if expense_transactions:
        largest_expense = max(expense_transactions, key=lambda tx: abs(float(tx["amount"] or 0)))
        largest_expense_currency = (largest_expense["currency_code"] or "UAH").upper()
        insights.append(
            {
                "icon": "\u20b4" if largest_expense_currency == "UAH" else largest_expense_currency,
                "title": "Largest recent expense",
                "text": (
                    f"{largest_expense['description'] or 'Recent expense'} for "
                    f"{abs(float(largest_expense['amount'] or 0)):.2f} {largest_expense_currency}."
                ),
            }
        )

    return insights[:3]


@_dashboard.route("/dashboard")
@login_required
def dashboard():
    """Обробляє маршрут `dashboard`."""
    user_id = get_userid()
    transactions = get_last_transactions(user_id)
    income_sum = get_sum_income(user_id)
    expense_sum = get_sum_expense(user_id)
    balance = income_sum - expense_sum

    categories_lookup = get_categories_lookup(user_id)
    accounts = account_service.get_accounts(user_id)
    budgets = budget_service.get_budgets(user_id)
    active_budgets = [budget for budget in budgets if budget.get("is_active")]
    savings_rate = round((balance / income_sum) * 100) if income_sum else 0
    dashboard_insights = _build_dashboard_insights(balance, income_sum, budgets, transactions)

    return render_template(
        "dashboard.html",
        username=get_username(),
        transactions=transactions,
        income_sum=income_sum,
        expense_sum=expense_sum,
        balance=balance,
        dashboard_currency="UAH",
        userID=user_id,
        categories_lookup=categories_lookup,
        accounts=accounts,
        budgets=budgets,
        active_budgets=active_budgets,
        dashboard_insights=dashboard_insights,
        savings_rate=savings_rate,
        current_month_label=datetime.now().strftime("%B %Y"),
        active_page="dashboard",
    )
