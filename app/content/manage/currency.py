from flask import Blueprint, request, render_template
from flask_login import login_required

_currency = Blueprint('currency', __name__)

@_currency.route('/currency', methods=['GET', 'POST'])
@login_required
def currency():
    return render_template('currency.html')
