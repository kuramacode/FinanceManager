from flask import Blueprint, render_template, request
from flask_login import login_required
from app.content.manage.category_service import get_expense_categories, get_income_categories
from app.utils.main_scripts import get_userid
_categories = Blueprint('category', __name__)

@_categories.route('/category', methods=['GET'])
@login_required
def category():
    """Обробляє маршрут `category`."""
    userid = get_userid()
    income_categories = get_income_categories(userid)
    expense_categories = get_expense_categories(userid)
    return render_template('categories.html',
                    income_categories=income_categories, expense_categories=expense_categories)
