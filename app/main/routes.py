from flask import Blueprint, render_template

_main = Blueprint('main', __name__)

@_main.route('/', methods=['GET'])
def main():
    """Обробляє маршрут `main`."""
    return render_template('main.html')
