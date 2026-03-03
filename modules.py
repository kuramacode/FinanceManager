from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy() # Ініціалізація SQLAlchemy

class User(UserMixin, db.Model): # Створення моделі користувача, яка наслідує UserMixin для інтеграції з Flask-Login
    id = db.column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем
    username = db.column(db.String(100), unique=True, nullable=False) # Визначення стовпця username як рядка з обмеженням унікальності та не допускає null
    email = db.column(db.String(100), unique=True, nullable=False) # Визначення стовпця email як рядка з обмеженням унікальності та не допускає null
    password = db.column(db.String(100), nullable=False) # Визначення стовпця password як рядка, який не допускає null