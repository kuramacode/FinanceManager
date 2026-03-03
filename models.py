from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy() # Ініціалізація SQLAlchemy

class User(UserMixin, db.Model): # Створення моделі користувача, яка наслідує UserMixin для інтеграції з Flask-Login
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключемted keyword argument 'primary_key'
    username = db.Column(db.String(100), unique=True, nullable=False) # Визначення стовпця username як рядка з обмеженням унікальності та не допускає null
    email = db.Column(db.String(100), unique=True, nullable=False) # Визначення стовпця email як рядка з обмеженням унікальності та не допускає null
    password = db.Column(db.String(100), nullable=False) # Визначення стовпця password як рядка, який не допускає null


class Transactions(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем    
    amount = db.Column(db.FLoat, nullable=False) # Визначення стовпця amount як числа з плаваючою точкою, який не допускає null
    date = db.Column(db.DateTime, nullable=False) # Визначення стовпця date як даты та времени, который не допускает null
    description = db.Column(db.String(255)) # Визначення стовпця description як рядка, который может быть null

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Визначення стовпця user_id як целого числа, который является внешним ключом, ссылающимся на id в таблице users, и не допускает null
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False) # Визначення стовпця category_id як целого числа, который является внешним ключом, ссылающимся на id в таблице categories, и не допускает null

class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем
    name = db.Column(db.String(100), unique=True, nullable=False) # Визначення стовпця name як рядка с ограничением уникальности и не допускающего null
