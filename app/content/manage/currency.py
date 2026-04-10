from flask import Blueprint, request, render_template
from flask_login import login_required
from  app.content.manage.currency_service import get_rates, get_nows_date

_currency = Blueprint('currency', __name__)

@_currency.route('/currency', methods=['GET', 'POST'])
@login_required
def currency():
    
    rates = get_rates(get_nows_date())[0]
    
    return render_template('currency.html',
                           rates=rates)
