import sys
import os
import types
import unittest
from datetime import datetime, timedelta
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
        """Ініціалізує допоміжний тестовий об’єкт."""
        self._value = _AnonymousUser()

    def set(self, user):
        """Зберігає поточного тестового користувача."""
        self._value = user

    def __getattr__(self, item):
        """Делегує доступ до атрибутів поточного користувача."""
        return getattr(self._value, item)

    def __bool__(self):
        """Повертає стан автентифікації тестового користувача."""
        return bool(getattr(self._value, "is_authenticated", False))


current_user = _CurrentUserProxy()


class UserMixin:
    @property
    def is_authenticated(self):
        """Повертає ознаку автентифікації у тестовому стабі."""
        return True


class LoginManager:
    def __init__(self):
        """Ініціалізує допоміжний тестовий менеджер авторизації."""
        self.login_view = None
        self._loader = None

    def init_app(self, app):
        """Під’єднує тестовий менеджер до застосунку."""
        self.app = app

    def user_loader(self, callback):
        """Реєструє тестовий loader користувача."""
        self._loader = callback
        return callback


def login_user(user):
    """Імітує вхід користувача у тестовому середовищі."""
    current_user.set(user)


def logout_user(user):
    """Імітує вихід користувача у тестовому середовищі."""
    current_user.set(_AnonymousUser())


def login_required(func):
    """Створює тестовий декоратор перевірки авторизації."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Обгортає тестову функцію перевіркою авторизації."""
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

from app import create_app
from app.models import Categories, Transactions, User, db
from tests.test_support import make_test_db_uri


class TestAppRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Готує спільне тестове оточення для всього класу тестів."""
        cls.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        """Очищає спільне тестове оточення після завершення класу тестів."""
        cls.ctx.pop()

    def setUp(self):
        """Готує тестове оточення перед виконанням кожного тесту."""
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = self.app.test_client()

    def _create_user(self, username="alice", email="alice@example.com", password="secret123"):
        """Створює допоміжні тестові дані користувача."""
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return user

    def _login(self, username="alice", password="secret123"):
        """Виконує тестовий вхід користувача."""
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_register_creates_user_and_redirects_to_login(self):
        """Перевіряє сценарій `register_creates_user_and_redirects_to_login`."""
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

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        created_user = User.query.filter_by(username="new_user").first()
        self.assertIsNotNone(created_user)

    def test_login_success_redirects_to_dashboard(self):
        """Перевіряє сценарій `login_success_redirects_to_dashboard`."""
        self._create_user()

        response = self._login()

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

    def test_login_shows_error_when_username_does_not_exist(self):
        """Перевіряє сценарій `login_shows_error_when_username_does_not_exist`."""
        response = self._login(username="missing_user", password="secret123")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No user with this username was found", response.data)
        self.assertIn(b'value="missing_user"', response.data)

    def test_login_shows_error_when_password_is_incorrect(self):
        """Перевіряє сценарій `login_shows_error_when_password_is_incorrect`."""
        self._create_user()

        response = self._login(password="wrong-password")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect password", response.data)

    def test_login_shows_errors_for_empty_fields(self):
        """Перевіряє сценарій `login_shows_errors_for_empty_fields`."""
        response = self.client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Enter your username", response.data)
        self.assertIn(b"Enter your password", response.data)

    def test_transactions_post_creates_transaction_record(self):
        """Перевіряє сценарій `transactions_post_creates_transaction_record`."""
        user = self._create_user()
        category = Categories(name="Food", user_id=user.id, emoji="🍔", type="expense", built_in=False)
        db.session.add(category)
        db.session.commit()

        self._login(username=user.username, password="secret123")

        response = self.client.post(
            "/transactions",
            data={
                "action": "create",
                "description": "Lunch",
                "amount": "123.45",
                "currency_code": "USD",
                "type": "expense",
                "category_id": str(category.id),
                "date": "2026-03-31",
                "time": "12:30",
                "return_filter": "all",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/transactions", response.headers["Location"])

        tx = Transactions.query.filter_by(user_id=user.id, description="Lunch").first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.type, "expense")
        self.assertEqual(tx.category_id, category.id)

    def test_history_page_renders_user_transactions(self):
        """Перевіряє сценарій `history_page_renders_user_transactions`."""
        user = self._create_user()
        category = Categories(name="Food", user_id=user.id, emoji="🍔", type="expense", built_in=False)
        db.session.add(category)
        db.session.commit()
        db.session.add(
            Transactions(
                amount=123.45,
                date=datetime(2026, 3, 31, 12, 30),
                description="Lunch",
                user_id=user.id,
                category_id=category.id,
                type="expense",
                currency_code="USD",
            )
        )
        db.session.commit()

        self._login(username=user.username, password="secret123")
        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lunch", response.data)
        self.assertIn(b"History - Ledger", response.data)

    def test_transactions_page_filters_by_custom_period(self):
        """Перевіряє сценарій `transactions_page_filters_by_custom_period`."""
        user = self._create_user()
        category = Categories(name="Food", user_id=user.id, emoji="🍔", type="expense", built_in=False)
        db.session.add(category)
        db.session.commit()
        now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        old_date = now - timedelta(days=45)
        db.session.add_all(
            [
                Transactions(
                    amount=10,
                    date=now,
                    description="Current period lunch",
                    user_id=user.id,
                    category_id=category.id,
                    type="expense",
                    currency_code="UAH",
                ),
                Transactions(
                    amount=20,
                    date=old_date,
                    description="Old period lunch",
                    user_id=user.id,
                    category_id=category.id,
                    type="expense",
                    currency_code="UAH",
                ),
            ]
        )
        db.session.commit()

        self._login(username=user.username, password="secret123")
        response = self.client.get(
            f"/transactions?period=custom&start={now.date().isoformat()}&end={now.date().isoformat()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Current period lunch", response.data)
        self.assertNotIn(b"Old period lunch", response.data)

    def test_dashboard_filters_by_custom_period(self):
        """Перевіряє сценарій `dashboard_filters_by_custom_period`."""
        user = self._create_user()
        category = Categories(name="Food", user_id=user.id, emoji="🍔", type="expense", built_in=False)
        db.session.add(category)
        db.session.commit()
        now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        old_date = now - timedelta(days=45)
        db.session.add_all(
            [
                Transactions(
                    amount=10,
                    date=now,
                    description="Dashboard current lunch",
                    user_id=user.id,
                    category_id=category.id,
                    type="expense",
                    currency_code="UAH",
                ),
                Transactions(
                    amount=20,
                    date=old_date,
                    description="Dashboard old lunch",
                    user_id=user.id,
                    category_id=category.id,
                    type="expense",
                    currency_code="UAH",
                ),
            ]
        )
        db.session.commit()

        self._login(username=user.username, password="secret123")
        response = self.client.get(
            f"/dashboard?period=custom&start={now.date().isoformat()}&end={now.date().isoformat()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard current lunch", response.data)
        self.assertNotIn(b"Dashboard old lunch", response.data)


if __name__ == "__main__":
    unittest.main()
