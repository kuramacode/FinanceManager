from flask import Blueprint, render_template, request, url_for, redirect
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from app.i18n import translate as t
from app.models.user import User

_auth= Blueprint('auth', __name__)

@_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Обробляє маршрут `login`."""
    errors = {}
    form_data = {"username": ""}

    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = request.form.get('password') or ""
        form_data["username"] = username

        if not username:
            errors["username"] = t("errors.username_required")
        if not password:
            errors["password"] = t("errors.password_required")

        if errors:
            return render_template('login.html', errors=errors, form_data=form_data)

        user = User.query.filter_by(username=username).first()

        if user is None:
            errors["username"] = t("errors.username_not_found")
        elif not check_password_hash(user.password, password):
            errors["password"] = t("errors.incorrect_password")
        else:
            login_user(user)
            return redirect(url_for('dashboard.dashboard'))

    return render_template('login.html', errors=errors, form_data=form_data)

@_auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Обробляє маршрут `logout`."""
    logout_user()
    return redirect(url_for('auth.login'))

