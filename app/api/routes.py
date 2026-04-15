from flask import Blueprint, request, jsonify
from app.services.converter import CurrencyConverter
from app.cache.rate import RateCache

_api = Blueprint("api", __name__)
cache = RateCache()
converter = CurrencyConverter(cache)


@_api.route("/convert", methods=['GET'])
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
    