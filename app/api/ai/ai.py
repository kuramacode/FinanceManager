from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.ai.service import AIService

_ai = Blueprint("ai", __name__, url_prefix="/api/ai")

@_ai.route('/expense-analysis', methods=['GET'])
@login_required
def expense_analysis():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    
    service = AIService()
    
    result = service.analyze_expenses(
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to
    )
    
    if not result.ok:
        return jsonify(result.model_dump()), 400
    
    return jsonify(result.model_dump()), 200