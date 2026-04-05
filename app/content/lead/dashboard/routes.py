from flask import Blueprint, render_template
from flask_login import login_required
from utils.main_scripts import get_userid, get_last_transactions, get_sum_expense, get_sum_income, get_username, get_categories_lookup

_dashboard = Blueprint('dashboard', __name__)

@_dashboard.route('/dashboard')
@login_required
def dashboard(): # Функція-обробник для відображення панелі керування користувача
    userId = get_userid()
    transactions = get_last_transactions(userId)
    income_sum = get_sum_income(userId)
    expense_sum = get_sum_expense(userId)
    balance = income_sum - expense_sum

    categories_lookup = get_categories_lookup(userId)
    return render_template('dashboard.html', username=get_username(),
                            transactions=transactions,
                            income_sum=income_sum, expense_sum=expense_sum,
                            balance=balance, userID=userId,
                            categories_lookup=categories_lookup)# Відображає шаблон 'dashboard.html' для користувача
