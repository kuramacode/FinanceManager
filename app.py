from flask import Flask, render_template, request, redirect, url_for, session, abort
# Імпорт об'єкта бази даних (db) та моделі користувача (User) з модуля modules
from models import db, User, Transactions, Categories
from config import Config
from utils.jinja_filters import color_change, format_date_for_website, category_name, category_emoji
from utils.main_scripts import *
# Імпорт функцій для управління автентифікацією та сесіями користувачів
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# Імпорт функцій для безпечного хешування та перевірки паролів
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import dotenv
import sqlite3

# Ініціалізація Flask додатка з назвою поточного модуля (__name__)
app = Flask(__name__)

app.config.from_object(Config)
app.jinja_env.filters['color'] = color_change
app.jinja_env.filters['format_date'] = format_date_for_website
app.jinja_env.filters['category_name'] = category_name
app.jinja_env.filters['category_emoji'] = category_emoji
app.jinja_env.filters['lenght'] = len
# Ініціалізація об'єкта бази даних SQLAlchemy з додатком Flask
db.init_app(app)

login_manager = LoginManager()# Створення об'єкта LoginManager для управління автентифікацією та сесіями користувачів
login_manager.init_app(app)# Ініціалізація менеджера входу з додатком Flask
login_manager.login_view = 'login'# Встановлення назви маршруту, на який буде перенаправлений незалогований користувач

@login_manager.user_loader # Декоратор, який реєструє функцію load_user для завантаження користувача за його ID

def load_user(user_id): # Ця функція викликається Flask-Login для отримання об'єкта користувача за його ID
    # Запит до бази даних: отримати користувача з заданим ID
    # int(user_id) - конвертація рядка ID в число
    return db.session.get(User, int(user_id)) 
    

# Контекст додатка необхідний для роботи з базою даних поза межами обробки запитів
with app.app_context():
    db.create_all() # Створює всі таблиці моделей бази даних (якщо вони ще не існують у БД)

# Декоратор встановлює маршрут для кореневої URL '/' (домашна сторінка)
@app.route('/', methods=['GET'])
def index(): # Функція-обробник для запитів на домашну сторінку
    return render_template('main.html')
# Декоратор встановлює маршрут '/register' для реєстрації користувачів
# methods=['GET', 'POST'] - приймає запити для відображення форми (GET) та обробки даних (POST)
@app.route('/register', methods=['GET', 'POST'])
def register(): # Функція-обробник для реєстрації нових користувачів
    # Перевіряє, чи це POST-запит (відправлення заповненої форми реєстрації)
    if request.method == 'POST':
        username, email, password, password_repeat = get_data_for_register()
        hash_password = generate_password_hash(password)# Хешує перший введений пароль для безпечного зберігання у БД
        
        if password != password_repeat:
                return 'Passwords do not match'# Повертає повідомлення про помилку, якщо паролі не збігаються
        else:
            user = User(username=username, email=email, password=hash_password)# Створює новий об'єкт користувача з введеними даними
            db.session.add(user) # Додає користувача до сесії бази даних (поки не збережено у БД)
            db.session.commit() # Фіксує зміни та зберігає користувача у базу даних
            return redirect(url_for('login'))# Перенаправляє користувача на сторінку входу після успішної реєстрації
        
    return render_template('register.html')

# Декоратор встановлює маршрут '/login' для входу користувачів
# methods=['GET', 'POST'] - приймає запити для відображення форми (GET) та обробки входу (POST)
@app.route('/login', methods=['GET', 'POST'])
def login(): # Функція-обробник для входу користувачів
    # Перевіряє, чи це POST-запит (відправлення форми входу з ім'ям та паролем)
    if request.method == 'POST':
        # Запит до бази даних: пошук першого користувача з таким ім'ям користувача
        username, password = get_data_for_login()
        user = User.query.filter_by(username=username).first()
        # Перевіряє, чи користувач існує (user != None) ТА чи пароль правильний
        # check_password_hash() порівнює хешований пароль з БД з введеним паролем
        if user and check_password_hash(user.password, password):
            
            login_user(user) # Создає сесію користувача та логує його в систему
            return redirect(url_for('dashboard')) # Перенаправляє користувача на панель керування після успішного входу
        else:
            return abort(401) # Якщо користувач не знайдений або пароль неправильний, повертає код помилки 403 (Forbidden)
    return render_template('login.html')
    
# Декоратор встановлює маршрут '/logout' для виходу користувачів
# methods=['GET', 'POST'] - приймає GET та POST запити для виходу
@app.route('/logout', methods=['GET', 'POST'])
# Декоратор @login_required - захищає маршрут від доступу незалогованих користувачів
# Незалогований користувач буде перенаправлений на сторінку входу
@login_required # Функція-обробник для виходу користувача з системи
def logout():
    logout_user()# Видаляє поточного користувача з сесії та завершує його сеанс
    return redirect(url_for('login'))# Перенаправляє користувача на сторінку входу після успішного виходу

@login_required
@app.route('/dashboard') # Декоратор встановлює маршрут '/dashboard' для доступу до панелі керування
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

@login_required
@app.route('/transactions', methods=['GET','POST']) # Декоратор встановлює маршрут '/transactions' для доступу до сторінки транзакцій
def transactions(): # Функція-обробник для відображення сторінки транзакцій користувача
    
    userId = get_userid() # Отримує ID поточного користувача за допомогою функції get_userid()
    
    if request.method == 'POST':
        amount, name, date, time, category, type = get_data_for_tx()

        
        amount = float(amount)
        category = int(category)
        n_date = normalized_date(str(date), str(time))

        tx = Transactions(
            amount=amount,
            date=n_date,
            description=name,
            user_id=userId,
            category_id=category,
            type=type,
        )

        db.session.add(tx)
        db.session.commit()

        return redirect(url_for('transactions'))


    filter = request.args.get('filter', 'all')
    filtered = filter_transactions(userId, filter)
    categories = get_categories(userId)
    categories_lookup = get_categories_lookup(userId)


    return render_template('transactions.html', transactions=filtered,
                           filter = filter,
                           username=get_username(), userID=userId,
                           categories=categories, categories_lookup=categories_lookup)# Відображає шаблон 'transactions.html' для користувача

if __name__ == '__main__':
    app.run(debug=True)
