import sys 
import os
import types
import unittest
from functools import wraps
from pathlib import Path

# Ensure sqlite directory exists for Config SQLAlchemy URI.
Path("/workspace/FinanceManager/instance").mkdir(parents=True, exist_ok=True)

# app/config imports dotenv; provide lightweight stub for test env.
dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)

# Provide a lightweight flask_login stub for environments without external deps.
flask_login_stub = types.ModuleType("flask_login")

class _AnonymousUser:
    id = None
    username = "" 
    is_authentificated = False

class _CurrentUserProxy:
    def __init__(self):
        self._value = _AnonymousUser()

    def set(self, user):
        self._value = user

    def __getattr__(self, item):
        return getattr(self._value, item)
    
    def __bool__(self):
        return bool(getattr(self._value, "is_authentificated", False))
    
current_user = _CurrentUserProxy()

class UserMixin:
    @property
    def is_authenticated(self):
        return True
    
class LoginManager:
    def __init__(self):
        self.login_view = None
        self._loader = None
    
    def init_app(self, app):
        self.app = app
    
    def user_loader(self, callback):
        self._loader = callback
        return callback

def login_user(user):
    current_user.set(user)

def logout_user(user):
    current_user.set(_AnonymousUser())

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            from flask import abort

            return abort(401)
        return func(*args, **kwargs)
    return wrapper

flask_login_stub.UserMixin = UserMixin
flask_login_stub.LoginManager = LoginManager
flask_login_stub.login_user = login_user
flask_login_stub.logout_user = logout_user
flask_login_stub.login_required = login_required
flask_login_stub.current_user = current_user
sys.modules.setdefault("flask_login", flask_login_stub)

from werkzeug.security import generate_password_hash

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Categories, Transactions

class TestAppRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()
    
    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = app.test_client()
    
    def _create_user(self, username="alice", email="alice@example.com", password="secret123"):
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    def _login(self, username="alice", password="secret123"):
        return self.client.post("/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )
    
    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            "/register",
            data={
                "username": "new_user",
                "email": "new_user@example.com",
                "password": "very_secret",
                "password_repeat": "very_secret",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code(302))
        self.assertIn("/login", response.headers["Location"])

        created_user = User.query.filter_by(username="new_user").first()
        self.assertIsNotNone(created_user)

    def test_login_success_redirects_to_dashboard(self):
        self._create_user()

        response = self._login()

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

    def test_transactions_post_creates_transaction_record(self):
        user = self._create_user()
        category = Categories(name="Food", user_id=user.id, emoji="🍔")
        db.session.add(category)
        db.session.commit()

        self._login(username=user.username, password="secretpass")

        response = self.client.post(
            "/transactions",
            data={
                "f_amount": "123.45",
                "f_name": "Lunch",
                "f_date": "2026-03-31",
                "f_time": "12:30",
                "f_category": str(category.id),
                "f_type": "expense",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/transactions", response.headers["Location"])

        tx = Transactions.query.filter_by(user_id=user.id, description="Lunch").first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.type, "expense")
        self.assertEqual(tx.category_id, category.id)


if __name__ == "__main__":
    unittest.main()

