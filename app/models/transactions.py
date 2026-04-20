from app.models.__init__ import db

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
