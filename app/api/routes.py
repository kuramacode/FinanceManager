from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.converter import CurrencyConverter
from app.services.category import Category_Service
from app.services.accounts import AccountService
from app.services.budget_services.budgets import BudgetService
from app.cache.rate import RateCache
from app.utils.main_scripts import get_userid

_api = Blueprint("api", __name__)
cache = RateCache()
converter = CurrencyConverter(cache)
category_service = Category_Service()
account_service = AccountService()
budget_service = BudgetService()


def _json_safe(value):
    """Виконує логіку функції `_json_safe`."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


@_api.route("/convert", methods=['GET'])
@login_required
def convert():
    """Конвертує дані у функції `convert`."""
    try:
        base_code = request.args.get("from")
        target_code = request.args.get("to")
        amount_param = request.args.get("amount")
         
        if not base_code:
            return jsonify({"error": "Parameter 'from' is required"}), 400

        if not target_code:
            return jsonify({"error": "Parameter 'to' is required"}), 400

        if amount_param is None:
            return jsonify({"error": "Parameter 'amount' is required"}), 400

        amount = float(amount_param)
        
        result = converter.convert(base_code, target_code, amount)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/category', methods=['GET'])
@login_required
def get_category():
    """Повертає дані у функції `get_category`."""
    try:
        user_id = get_userid()
        response = category_service.get_categories(user_id)
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/category', methods=['POST'])
@login_required
def create_category():
    """Створює дані у функції `create_category`."""
    try:
        user_id = get_userid()
        data = request.get_json()
        
        name = (data.get('name') or '').strip()
        desc = (data.get('desc') or '').strip()
        emoji = (data.get('emoji') or '🛒').strip()
        type_ = (data.get('type') or 'expense').strip()
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
        if type_ not in ('expense', 'income', 'transfer'):
            # FIX: was missing status code 400
            return jsonify({"error": "Type must be 'expense', 'income' or 'transfer'"}), 400

        category = category_service.create_category(user_id, name, desc, emoji, type_)
        return jsonify(category), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400 
        
@_api.route('/category/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """Оновлює дані у функції `update_category`."""
    try:
        user_id = get_userid()
        data = request.get_json()
        
        name = (data.get('name') or '').strip()
        desc = (data.get('desc') or '').strip()
        emoji = (data.get('emoji') or '🛒').strip()
        type_ = (data.get('type') or 'expense').strip()
      
        if not name:
            return jsonify({"error": "Name is required"}), 400
        if type_ not in ('expense', 'income', 'transfer'):
            return jsonify({"error": "Type must be 'expense', 'income' or 'transfer'"}), 400
        
        category = category_service.update_category(category_id, user_id, name, desc, emoji, type_)
        if category is None:
            return jsonify({"error": "Category not found or access denied"}), 404
        
        return jsonify(category), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@_api.route('/category/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """Видаляє дані у функції `delete_category`."""
    try:
        user_id = get_userid()
        success = category_service.delete_category(category_id, user_id)
        
        if not success:
            return jsonify({"error": "Category not found or access denied"}), 404
        
        return jsonify({"deleted": category_id}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/accounts', methods=['GET'])
@login_required
def accounts():
    """Обробляє маршрут `accounts`."""
    try:
        user_id = get_userid()
        response = account_service.get_accounts(user_id)
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/accounts', methods=['POST'])
@login_required
def create_account():
    """Створює дані у функції `create_account`."""
    try:
        user_id = get_userid()
        data = request.get_json()
        
        name = (data.get('name') or '').strip()
        balance = float(data.get('balance') or 0)
        status = (data.get('status') or 'active').strip()
        currency_code = (data.get('currency_code') or 'UAH').strip()
        emoji = (data.get('emoji') or '💸').strip()
        type = (data.get('type') or 'card').strip()
        subtitle = (data.get('subtitle') or '').strip()
        note = (data.get('note') or '').strip()
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
        if status not in ('active', 'frozen', 'closed'):
            return jsonify({"error": "Status must be 'active', 'frozen' or 'closed'"}), 400

        response = account_service.create_account(user_id, name, balance, status, currency_code, emoji, type, subtitle, note)
        # FIX: was returning 200 instead of 201
        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@_api.route('/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    """Оновлює дані у функції `update_account`."""
    try:
        user_id = get_userid()
        data = request.get_json()
        
        name = (data.get('name') or '').strip()
        balance = float(data.get('balance') or 0)
        status = (data.get('status') or 'active').strip()
        currency_code = (data.get('currency_code') or 'UAH').strip()
        emoji = (data.get('emoji') or '💸').strip()
        type = (data.get('type') or 'card').strip()
        subtitle = (data.get('subtitle') or '').strip()
        note = (data.get('note') or '').strip()
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
        if status not in ('active', 'frozen', 'closed'):
            return jsonify({"error": "Status must be 'active', 'frozen' or 'closed'"}), 400

        response = account_service.update_account(account_id, user_id, name, balance, status, currency_code, emoji, type, subtitle, note)

        # FIX: was missing the None check — always returned 200 even when account not found
        if response is None:
            return jsonify({"error": "Account not found or access denied"}), 404
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@_api.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    """Видаляє дані у функції `delete_account`."""
    try:
        user_id = get_userid()
        success = account_service.delete_account(account_id, user_id)
        if not success:
            return jsonify({"error": "Account not found or access denied"}), 404
        
        return jsonify({"deleted": account_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@_api.route('/budgets', methods=['GET'])
@login_required
def get_budgets():
    """Повертає дані у функції `get_budgets`."""
    try:
        user_id = get_userid()
        budgets = budget_service.get_budgets(user_id)
        return jsonify(_json_safe(budgets)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@_api.route('/budgets', methods=['POST'])
@login_required
def create_budget():
    """Створює дані у функції `create_budget`."""
    try:
        user_id = get_userid()
        data = request.get_json() or {}

        budget = budget_service.create_budget(
            user_id,
            name=data.get('name'),
            desc=data.get('desc'),
            amount_limit=data.get('amount_limit'),
            currency_code=data.get('currency_code'),
            period_type=data.get('period_type'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            category_ids=data.get('category_ids') or [],
        )
        return jsonify(_json_safe(budget)), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@_api.route('/budgets/<int:budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    """Оновлює дані у функції `update_budget`."""
    try:
        user_id = get_userid()
        data = request.get_json() or {}

        budget = budget_service.update_budget(
            budget_id,
            user_id,
            name=data.get('name'),
            desc=data.get('desc'),
            amount_limit=data.get('amount_limit'),
            currency_code=data.get('currency_code'),
            period_type=data.get('period_type'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            category_ids=data.get('category_ids') or [],
        )

        if budget is None:
            return jsonify({"error": "Budget not found or access denied"}), 404

        return jsonify(_json_safe(budget)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@_api.route('/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Видаляє дані у функції `delete_budget`."""
    try:
        user_id = get_userid()
        success = budget_service.delete_budget(budget_id, user_id)

        if not success:
            return jsonify({"error": "Budget not found or access denied"}), 404

        return jsonify({"deleted": budget_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
