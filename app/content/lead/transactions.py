from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from app.utils.main_scripts import get_userid, normalized_date, get_data_for_tx, get_categories, get_username, filter_transactions, get_categories_lookup
from app.models import db, Transactions

_transactions = Blueprint('transactions', __name__)

@_transactions.route('/transactions', methods=['GET', 'POST'])
@login_required
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

        return redirect(url_for('transactions.transactions'))


    filter = request.args.get('filter', 'all')
    filtered = filter_transactions(userId, filter)
    categories = get_categories(userId)
    categories_lookup = get_categories_lookup(userId)


    return render_template('transactions.html', transactions=filtered,
                           filter = filter,
                           username=get_username(), userID=userId,
                           categories=categories, categories_lookup=categories_lookup)# Відображає шаблон 'transactions.html' для користувача
