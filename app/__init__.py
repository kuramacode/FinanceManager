from flask import Flask
from flask_login import LoginManager
from app.config import Config
from app.utils.jinja_filters import color_change, format_date_for_website,category_name, category_emoji, currency_flag, get_difference_percentage, get_difference
from app.utils.main_scripts import get_username
from app.models import db, User
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_object(Config)
    app.jinja_env.filters['color'] = color_change
    app.jinja_env.filters['format_date'] = format_date_for_website
    app.jinja_env.filters['category_name'] = category_name
    app.jinja_env.filters['category_emoji'] = category_emoji
    app.jinja_env.filters['lenght'] = len
    app.jinja_env.filters['currency_flag'] = currency_flag
    app.jinja_env.filters['to_lower'] = str.lower 
    
    app.jinja_env.globals['rate_difference'] = get_difference_percentage
    app.jinja_env.globals['difference'] = get_difference
    app.jinja_env.globals['username'] = get_username
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    db.init_app(app)
    blueprints = []
    from app.main.routes import _main; blueprints.append(_main)
    from app.auth.routes import _auth; blueprints.append(_auth)
    from app.register.routes import _register; blueprints.append(_register)
    from app.content.lead.dashboard import _dashboard; blueprints.append(_dashboard)
    from app.content.lead.transactions import _transactions; blueprints.append(_transactions)
    from app.content.manage.currency import _currency; blueprints.append(_currency)
    from app.content.manage.category import _categories; blueprints.append(_categories)
    from app.api.routes import _api
    app.register_blueprint(_api, url_prefix="/api")
    for br in blueprints:
        app.register_blueprint(br)
    
    with app.app_context():
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db.create_all()

    
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))