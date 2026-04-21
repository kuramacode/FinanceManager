from datetime import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from app.content.lead.dashboard_service import get_last_transactions, get_sum_expense, get_sum_income
from app.i18n import format_month_year, translate as t
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
                    "title": t("dashboard.insight_income_covering_title"),
                    "text": t("dashboard.insight_income_covering_text", rate=savings_rate),
                }
            )
        else:
            insights.append(
                {
                    "icon": "!",
                    "title": t("dashboard.insight_expenses_ahead_title"),
                    "text": t("dashboard.insight_expenses_ahead_text", rate=savings_rate),
                }
            )

    exceeded_budget = next((budget for budget in budgets if budget.get("status") == "exceeded"), None)
    if exceeded_budget is not None:
        insights.append(
            {
                "icon": "!",
                "title": t("dashboard.insight_budget_over_title", name=exceeded_budget["name"]),
                "text": t(
                    "dashboard.insight_budget_over_text",
                    spent=f"{exceeded_budget['spent']:.2f}",
                    limit=f"{exceeded_budget['amount_limit']:.2f}",
                    currency=exceeded_budget["currency_code"],
                ),
            }
        )
    else:
        warning_budget = next((budget for budget in budgets if budget.get("status") == "warning"), None)
        if warning_budget is not None:
            insights.append(
                {
                    "icon": "•",
                    "title": t("dashboard.insight_budget_warning_title", name=warning_budget["name"]),
                    "text": t("dashboard.insight_budget_warning_text", percent=f"{warning_budget['percent']:.0f}"),
                }
            )

    expense_transactions = [tx for tx in transactions if (tx["type"] or "").lower() == "expense"]
    if expense_transactions:
        largest_expense = max(expense_transactions, key=lambda tx: abs(float(tx["amount"] or 0)))
        largest_expense_currency = (largest_expense["currency_code"] or "UAH").upper()
        insights.append(
            {
                "icon": "\u20b4" if largest_expense_currency == "UAH" else largest_expense_currency,
                "title": t("dashboard.insight_largest_expense_title"),
                "text": t(
                    "dashboard.insight_largest_expense_text",
                    description=largest_expense["description"] or t("dashboard.recent_expense"),
                    amount=f"{abs(float(largest_expense['amount'] or 0)):.2f}",
                    currency=largest_expense_currency,
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
        current_month_label=format_month_year(datetime.now()),
        active_page="dashboard",
    )
