from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.converter import CurrencyConverter
from app.services.category import Category_Service
from app.cache.rate import RateCache
from app.utils.main_scripts import get_userid

_api = Blueprint("api", __name__)
cache = RateCache()
converter = CurrencyConverter(cache)
category_service = Category_Service()


@_api.route("/convert", methods=['GET'])
@login_required
def convert():
    try:
        base_code = request.args.get("from")
        target_code = request.args.get("to")
        amount = float(request.args.get("amount"))
        
        if not base_code:
            return jsonify({"error": "Parameter 'from' is required"}), 400

        if not target_code:
            return jsonify({"error": "Parameter 'to' is required"}), 400

        if not amount:
            return jsonify({"error": "Parameter 'amount' is required"}), 400
        
        
        result = converter.convert(base_code, target_code, amount)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/category', methods=['GET'])
@login_required
def get_category():
    try:
        user_id = get_userid()
        
        response = category_service.get_categories(user_id)
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@_api.route('/category', methods=['POST'])
@login_required
def create_category():
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
                return jsonify({"error": "Type must be 'expense', 'income' or 'transfer'"})

            category = category_service.create_category(user_id, name, desc, emoji, type_)
            
            return jsonify(category), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400 
        
@_api.route('/category/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
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
            return jsonify({"error": "Type must be 'expense', 'income' or 'transfer'"})
        
        category = category_service.update_category(category_id, user_id, name, desc, emoji, type_)
        if category is None:
            return jsonify({"error": "Category not found or access denied"}), 404
        
        return jsonify(category), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
        

@_api.route('/category/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    try:
        user_id = get_userid()
        success = category_service.delete_category(category_id, user_id)
        
        if not success:
            return jsonify({"error": "Category not found or access denied"}), 404
        
        return jsonify({"deleted": category_id}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400