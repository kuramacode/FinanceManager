from flask import Blueprint, render_template
from flask_login import login_required

_accounts = Blueprint('accounts', __name__)

@_accounts.route('/accounts', methods=['GET'])
def accounts():
    """Обробляє маршрут `accounts`."""
    return render_template('accounts.html')
