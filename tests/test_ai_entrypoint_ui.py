import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import User, db
from tests.test_support import make_test_db_uri


class TestAiEntrypointUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "ai-entrypoint-test-secret",
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def setUp(self):
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = self.app.test_client()

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
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_budgets_page_uses_shared_ai_entrypoint_shell(self):
        user = self._create_user()
        self._login(user.username, "secret123")

        response = self.client.get("/budgets")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="aiEntrypoint"', html)
        self.assertIn('data-page-key="budgets"', html)
        self.assertIn("Analyze budgets", html)
        self.assertIn("Overspending risk", html)
        self.assertIn("ai-entrypoint.js", html)

    def test_transactions_page_renders_transactions_specific_ai_actions(self):
        user = self._create_user()
        self._login(user.username, "secret123")

        response = self.client.get("/transactions")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="aiEntrypointLauncher"', html)
        self.assertIn('data-page-key="transactions"', html)
        self.assertIn("Analyze transactions", html)
        self.assertIn("Recurring payments", html)
        self.assertIn("Expense optimization tips", html)


if __name__ == "__main__":
    unittest.main()
