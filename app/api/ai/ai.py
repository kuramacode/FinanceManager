from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.ai.service import AIService
from app.i18n import get_current_language

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
        date_to=date_to,
        language=get_current_language(),
    )
    
    if not result.ok:
        return jsonify(result.model_dump()), 400
    
    return jsonify(result.model_dump()), 200


@_ai.route("/actions/<action_id>", methods=["POST"])
@login_required
def run_action(action_id):
    payload = request.get_json(silent=True) or {}

    service = AIService()
    result = service.run_action(
        user_id=current_user.id,
        action_id=action_id,
        page_key=payload.get("page_key") or request.args.get("page"),
        message=payload.get("message"),
        language=get_current_language(),
    )

    if not result.ok:
        return jsonify(result.model_dump()), 400

    return jsonify(result.model_dump()), 200
