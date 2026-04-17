from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy() # Ініціалізація SQLAlchemy

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

class Transactions(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем    
    amount = db.Column(db.Numeric(12, 2), nullable=False) # Визначення стовпця amount як числа з плаваючою точкою, який не допускає null
    date = db.Column(db.DateTime, nullable=False) # Визначення стовпця date як даты та времени, который не допускает null
    description = db.Column(db.String(255)) # Визначення стовпця description як рядка, который может быть null

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Визначення стовпця user_id як целого числа, который является внешним ключом, ссылающимся на id в таблице users, и не допускает null
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False) # Визначення стовпця category_id як целого числа, который является внешним ключом, ссылающимся на id в таблице categories, и не допускает null
    type = db.Column(db.String(100), nullable=False) # income, expense, transfer
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True) # Визначення стовпця account_id як целого числа, который является внешним ключом, ссылающимся на id в таблице accounts, и допускает null (для транзакций типа transfer)
    currency_code = db.Column(db.String(3), nullable=False, default='UAH')
class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True) # Визначення стовпця id як цілого числа, який є первинним ключем
    name = db.Column(db.String(100), nullable=False) # Визначення стовпця name як рядка с ограничением уникальности и не допускающего null
    desc = db.Column(db.String(255))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id') ,nullable=False)
    emoji = db.Column(db.String(8), default='📦')
    built_in = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(20), nullable=False) # 'income' або 'expense'
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name'),
    )
    
class Currency(db.Model):
    __tablename__ = 'currencies'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(20), unique=True, nullable=False)
    flag = db.Column(db.String(3), unique=True, nullable=False)
    
class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    base_code = db.Column(db.String(3), nullable=False, default='UAH')   # UAH
    target_code = db.Column(db.String(3), nullable=False) # USD
    rate = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(32))  # 'nbu', 'monobank', тощо
    
    __table_args__ = (
        db.UniqueConstraint('base_code', 'target_code', 'date', 'source'),
    )
    
class Accounts(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='active') # active, frozen, closed
    currency_code = db.Column(db.String(20), nullable=False, default='UAH')
    emoji = db.Column(db.String(3), default='💸')
    type = db.Column(db.String(20), default='card')
    subtitle = db.Column(db.String(255))
    note = db.Column(db.String(255))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Budget(db.Model):
    __tablename__ = "budgets"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(255))
    
    amount_limit = db.Column(db.Numeric(12, 2), nullable=False)
    currency_code = db.Column(db.String(3), nullable=False, default="UAH")
    
    period_type = db.Column(db.String(20), default='monthly')
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
class BudgetCategory(db.Model):
    __tablename__ = "budget_categories"
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey("budgets.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    