from flask import Blueprint, render_template
from flask_login import login_required

_budgets = Blueprint('budgets', __name__)

@_budgets.route('/budgets', methods=['GET'])
@login_required
def budgets():
    return render_template('budgets.html')
