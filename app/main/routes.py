from flask import Blueprint, redirect, render_template, request, url_for

from app.i18n import is_safe_redirect_target, normalize_language, set_language_cookie

_main = Blueprint("main", __name__)


@_main.route("/", methods=["GET"])
def main():
    """Renders the public landing page."""
    return render_template("main.html")


@_main.route("/language/<language>", methods=["POST"])
def set_language(language):
    normalized = normalize_language(language) or "en"
    next_url = request.form.get("next") or request.referrer or url_for("main.main")
    if not is_safe_redirect_target(next_url):
        next_url = url_for("main.main")

    response = redirect(next_url)
    return set_language_cookie(response, normalized)
