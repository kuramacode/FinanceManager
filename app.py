from flask import Flask, render_template, request, redirect, url_for
# Імпорт об'єкта бази даних (db) та моделі користувача (User) з модуля modules
from modules import db, User
# Імпорт функцій для управління автентифікацією та сесіями користувачів
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# Імпорт функцій для безпечного хешування та перевірки паролів
from werkzeug.security import generate_password_hash, check_password_hash
import os
import dotenv

# Завантажує всі змінні середовища з файлу .env у поточний процес
dotenv.load_dotenv()

# Ініціалізація Flask додатка з назвою поточного модуля (__name__)
app = Flask(__name__)

# Встановлення секретного ключа для шифрування даних сесій користувачів (отримується з .env файлу)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Встановлення адреси підключення до бази даних SQLite (отримується з .env файлу)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

# Ініціалізація об'єкта бази даних SQLAlchemy з додатком Flask
db.init_app(app)

login_manager = LoginManager()# Створення об'єкта LoginManager для управління автентифікацією та сесіями користувачів
login_manager.init_app(app)# Ініціалізація менеджера входу з додатком Flask
login_manager.login_view = 'login'# Встановлення назви маршруту, на який буде перенаправлений незалогований користувач

@login_manager.user_loader # Декоратор, який реєструє функцію load_user для завантаження користувача за його ID

def load_user(user_id): # Ця функція викликається Flask-Login для отримання об'єкта користувача за його ID
    # Запит до бази даних: отримати користувача з заданим ID
    # int(user_id) - конвертація рядка ID в число
    return User.query.get(int(user_id)) 

# Контекст додатка необхідний для роботи з базою даних поза межами обробки запитів
with app.app_context():
    db.create_all() # Створює всі таблиці моделей бази даних (якщо вони ще не існують у БД)

# Декоратор встановлює маршрут для кореневої URL '/' (домашна сторінка)
@app.route('/')
def index(): # Функція-обробник для запитів на домашну сторінку
    return render_template('main.html')
# Декоратор встановлює маршрут '/register' для реєстрації користувачів
# methods=['GET', 'POST'] - приймає запити для відображення форми (GET) та обробки даних (POST)
@app.route('/register', methods=['GET', 'POST'])
def register(): # Функція-обробник для реєстрації нових користувачів
    username = request.form['username']# Отримує значення 'username' з даних форми, відправленої користувачем
    email = request.form['email']# Отримує значення 'email' з даних форми
    hash_password = generate_password_hash(request.form['password'])# Хешує перший введений пароль для безпечного зберігання у БД
    hash_password2 = generate_password_hash(request.form['password_repeat'])# Хешує повторно введений пароль для перевірки збігу паролів
    
    # Перевіряє, чи це POST-запит (відправлення заповненої форми реєстрації)
    if request.method == 'POST':
        if request.form['password'] != request.form['password_repeat']:
            return 'Passwords do not match'# Повертає повідомлення про помилку, якщо паролі не збігаються
        else:
            user = User(username=username, email=email, password=hash_password)# Створює новий об'єкт користувача з введеними даними
            db.session.add(user)# Додає користувача до сесії бази даних (поки не збережено у БД)
            db.session.commit()# Фіксує зміни та зберігає користувача у базу даних
            return redirect(url_for('login'))# Перенаправляє користувача на сторінку входу після успішної реєстрації
    
    return render_template('register.html')

# Декоратор встановлює маршрут '/login' для входу користувачів
# methods=['GET', 'POST'] - приймає запити для відображення форми (GET) та обробки входу (POST)
@app.route('/login', methods=['GET', 'POST'])
def login(): # Функція-обробник для входу користувачів
    # Перевіряє, чи це POST-запит (відправлення форми входу з ім'ям та паролем)
    if request.method == 'POST':
        # Запит до бази даних: пошук першого користувача з таким ім'ям користувача
        user = User.query.filter_by(username=request.form['username']).first()
        # Перевіряє, чи користувач існує (user != None) ТА чи пароль правильний
        # check_password_hash() порівнює хешований пароль з БД з введеним паролем
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user) # Создає сесію користувача та логує його в систему
            return redirect(url_for('main'))
        else:
            return 403 # Якщо користувач не знайдений або пароль неправильний, повертає код помилки 403 (Forbidden)
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

if __name__ == '__main__':
    app.run(debug=True)
