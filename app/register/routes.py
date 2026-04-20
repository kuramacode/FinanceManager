from flask import Blueprint, request, redirect, url_for, render_template
from app.models import db
from app.models.user import User
from werkzeug.security import generate_password_hash
from ..utils.main_scripts import get_data_for_register

_register = Blueprint('register', __name__)

@_register.route('/register', methods=['GET', 'POST'])
def register(): # Функція-обробник для реєстрації нових користувачів
    # Перевіряє, чи це POST-запит (відправлення заповненої форми реєстрації)
    """Обробляє маршрут `register`."""
    if request.method == 'POST':
        username, email, password, password_repeat = get_data_for_register()
        hash_password = generate_password_hash(password)# Хешує перший введений пароль для безпечного зберігання у БД
        
        if password != password_repeat:
                return 'Passwords do not match'# Повертає повідомлення про помилку, якщо паролі не збігаються
        else:
            user = User(username=username, email=email, password=hash_password)# Створює новий об'єкт користувача з введеними даними
            db.session.add(user) # Додає користувача до сесії бази даних (поки не збережено у БД)
            db.session.commit() # Фіксує зміни та зберігає користувача у базу даних
            return redirect(url_for('auth.login'))# Перенаправляє користувача на сторінку входу після успішної реєстрації
        
    return render_template('register.html')
