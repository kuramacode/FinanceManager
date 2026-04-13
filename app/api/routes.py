from flask import Blueprint, request, jsonify
from app.services.converter import CurrencyConverter

_api = Blueprint("api", __name__)
converter = CurrencyConverter()

@_api.route("/convert", methods=['GET'])
def convert():
    try:
        base_code = request.args.get("from")
        target_code = request.args.get("to")
        amount = float(request.args.get("amount"))
        
        result = converter.convert(base_code, target_code, amount)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    