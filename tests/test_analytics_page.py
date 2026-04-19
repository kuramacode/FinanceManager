from datetime import date, datetime
import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Accounts, Budget, BudgetCategory, Categories, Transactions, User, db
from tests.test_support import make_test_db_uri


class TestAnalyticsPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configures the shared analytics test app."""
        cls.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "analytics-test-secret",
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        """Releases the shared analytics test context."""
        cls.ctx.pop()

    def setUp(self):
        """Resets the database before each analytics test."""
        db.session.remove()
        db.drop_all()
        db.create_all()
        self.client = self.app.test_client()

    def _create_user(self, username="alice", email="alice@example.com", password="secret123"):
        """Creates a test user."""
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return user

    def _create_category(self, user_id, name, type_):
        """Creates a test category."""
        category = Categories(
            name=name,
            user_id=user_id,
            emoji=name[:1].upper(),
            type=type_,
            built_in=False,
        )
        db.session.add(category)
        db.session.commit()
        return category

    def _create_account(self, user_id, name="Wallet", currency_code="USD", balance=0):
        """Creates a test account."""
        account = Accounts(
            name=name,
            balance=balance,
            status="active",
            currency_code=currency_code,
            emoji=name[:1].upper(),
            type="cash",
            subtitle="Primary",
            user_id=user_id,
        )
        db.session.add(account)
        db.session.commit()
        return account

    def _create_budget(self, user_id, category_id, name="Food budget", currency_code="USD"):
        """Creates a test budget linked to one category."""
        budget = Budget(
            user_id=user_id,
            name=name,
            desc="Monthly limit",
            amount_limit=500,
            currency_code=currency_code,
            period_type="monthly",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
        )
        db.session.add(budget)
        db.session.commit()

        db.session.add(BudgetCategory(budget_id=budget.id, category_id=category_id))
        db.session.commit()
        return budget

    def _login(self, username="alice", password="secret123"):
        """Signs in the test user."""
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_get_analytics_page_renders_real_embedded_data(self):
        """Ensures the analytics page embeds real project data sources."""
        user = self._create_user()
        expense_category = self._create_category(user.id, "Food", "expense")
        income_category = self._create_category(user.id, "Salary", "income")
        account = self._create_account(user.id, balance=1250)
        self._create_budget(user.id, expense_category.id)

        db.session.add(
            Transactions(
                amount=42.5,
                date=datetime(2026, 4, 17, 12, 30),
                description="Lunch",
                user_id=user.id,
                category_id=expense_category.id,
                type="expense",
                account_id=account.id,
                currency_code="USD",
            )
        )
        db.session.add(
            Transactions(
                amount=1800,
                date=datetime(2026, 4, 18, 9, 0),
                description="Salary payout",
                user_id=user.id,
                category_id=income_category.id,
                type="income",
                account_id=account.id,
                currency_code="USD",
            )
        )
        db.session.commit()

        self._login(user.username, "secret123")
        response = self.client.get("/analytics")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="analytics-transactions-data"', html)
        self.assertIn('id="analytics-accounts-data"', html)
        self.assertIn('id="analytics-budgets-data"', html)
        self.assertIn("Lunch", html)
        self.assertIn("Salary payout", html)
        self.assertIn("Wallet", html)
        self.assertIn("Food budget", html)
        self.assertIn('data-primary-currency="USD"', html)


if __name__ == "__main__":
    unittest.main()
