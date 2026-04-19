from flask import Blueprint, render_template
from flask_login import login_required

from app.content.lead.analytics_service import build_analytics_payload
from app.utils.main_scripts import get_userid, get_username

_analytics = Blueprint("analytics", __name__)


@_analytics.route("/analytics")
@login_required
def analytics():
    """Renders the analytics page with real project data."""
    user_id = get_userid()
    payload = build_analytics_payload(user_id)

    return render_template(
        "analytics.html",
        username=get_username(),
        userID=user_id,
        active_page="analytics",
        available_currencies=payload["available_currencies"],
        primary_currency=payload["primary_currency"],
        analytics_transactions=payload["transactions"],
        analytics_categories=payload["categories"],
        analytics_accounts=payload["accounts"],
        analytics_budgets=payload["budgets"],
    )
