from app.models.__init__ import db
from flask_login import UserMixin

class User(UserMixin, db.Model): # Створення моделі користувача, яка наслідує UserMixin для інтеграції з Flask-Login
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключемted keyword argument 'primary_key'
    username = db.Column(db.String(100), unique=True, nullable=False) # Визначення стовпця username як рядка з обмеженням унікальності та не допускає null
    email = db.Column(db.String(100), unique=True, nullable=False) # Визначення стовпця email як рядка з обмеженням унікальності та не допускає null
    password = db.Column(db.String(100), nullable=False) # Визначення стовпця password як рядка, який не допускає null
    role = db.Column(db.String(20), nullable=False, default='user') # Визначення стовпця role як рядка, который не допускает null и имеет значение по умолчанию 'user'
    type = db.Column(db.String(20), nullable=False, default='personal') # personal, business
    
    transactions = db.relationship('Transactions', backref='user', lazy=True) # Встановлення зв'язку один-до-багатьох між користувачем та транзакціями, з можливістю доступу до транзакцій через атрибут 'transactions' та зворотного доступу до користувача через атрибут 'user' у моделі Transactions
    categories = db.relationship('Categories', backref='user', lazy=True)
