from flask import Blueprint, render_template
from flask_login import login_required

from app.utils.main_scripts import get_username, get_userid

_accounts = Blueprint("accounts", __name__)


@_accounts.route("/accounts", methods=["GET"])
@login_required
def accounts():
    """Renders the accounts page."""
    return render_template(
        "accounts.html",
        username=get_username(),
        userID=get_userid(),
        active_page="accounts",
    )
