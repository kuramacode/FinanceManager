from flask import Blueprint, render_template, request, url_for, redirect, abort
from flask_login import login_user, login_required, logout_user
from app.utils.main_scripts import get_data_for_login
from werkzeug.security import check_password_hash
from app.models import db
from app.models.user import User

_auth= Blueprint('auth', __name__)

@_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Обробляє маршрут `login`."""
    if request.method == 'POST':
        
        username, password = request.form.get('username'), request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard.dashboard'))
        else:
            return abort(401)
        
    return render_template('login.html')

@_auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Обробляє маршрут `logout`."""
    logout_user()
    return redirect(url_for('auth.login'))

