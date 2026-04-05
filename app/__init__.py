from flask import Flask
from flask_login import LoginManager
from app.config import Config
from app.utils.jinja_filters import color_change, format_date_for_website,category_name, category_emoji
from app.models import db, User

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    app.jinja_env.filters['color'] = color_change
    app.jinja_env.filters['format_date'] = format_date_for_website
    app.jinja_env.filters['category_name'] = category_name
    app.jinja_env.filters['category_emoji'] = category_emoji
    app.jinja_env.filters['lenght'] = len
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    db.init_app(app)
    
    from app.main.routes import _main
    from app.auth.routes import _auth
    from app.register.routes import _register
    from app.content.lead.dashboard.routes import _dashboard
    from app.content.lead.transactions.routes import _transactions
    
    app.register_blueprint(_main)
    app.register_blueprint(_auth)
    app.register_blueprint(_register)
    app.register_blueprint(_dashboard)
    app.register_blueprint(_transactions)
    
    with app.app_context():
        db.create_all()
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))