from flask import Blueprint, request, render_template
from flask_login import login_required
from  app.content.manage.currency_service import get_rates, get_nows_date
from app.utils.consts import MAIN_CURRENCIES

_currency = Blueprint('currency', __name__)

@_currency.route('/currency', methods=['GET', 'POST'])
@login_required
def currency():
    """Обробляє маршрут `currency`."""
    try:
        rates = get_rates(get_nows_date(), MAIN_CURRENCIES)[0]
    except Exception as e:
        raise MemoryError
    
    return render_template('currency.html',
                           rates=rates)
