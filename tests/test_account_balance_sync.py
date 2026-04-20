from datetime import datetime
import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Categories, Transactions, User, db
from tests.test_support import make_test_db_uri


class TestAccountBalanceSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configures the shared app for account balance synchronization tests."""
        cls.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "account-balance-secret",
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        """Releases the shared app context."""
        cls.ctx.pop()

    def setUp(self):
        """Resets the database before each balance sync test."""
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
        """Creates a category for transaction scenarios."""
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

    def _login(self, username="alice", password="secret123"):
        """Signs in the test user."""
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def _create_account_via_api(self, *, name, initial_balance, currency_code="USD", type_="cash"):
        """Creates an account through the public API."""
        response = self.client.post(
            "/api/accounts",
            json={
                "name": name,
                "initial_balance": initial_balance,
                "status": "active",
                "currency_code": currency_code,
                "emoji": name[:1].upper(),
                "type": type_,
                "subtitle": "",
                "note": "",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def _accounts_by_name(self):
        """Returns API accounts keyed by name for easier assertions."""
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        return {account["name"]: account for account in response.get_json()}

    def test_account_balance_tracks_transaction_lifecycle(self):
        """Balances stay consistent through create, update, move, and delete operations."""
        user = self._create_user()
        expense_category = self._create_category(user.id, "Food", "expense")
        income_category = self._create_category(user.id, "Salary", "income")
        self._login(user.username, "secret123")

        wallet = self._create_account_via_api(name="Wallet", initial_balance=1000)
        bank = self._create_account_via_api(name="Bank", initial_balance=300, type_="bank")

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["initial_balance"], 1000.0)
        self.assertEqual(accounts["Wallet"]["balance"], 1000.0)
        self.assertEqual(accounts["Bank"]["balance"], 300.0)

        create_response = self.client.post(
            "/transactions",
            data={
                "action": "create",
                "description": "Groceries",
                "amount": "120",
                "currency_code": "USD",
                "type": "expense",
                "category_id": str(expense_category.id),
                "account_id": str(wallet["id"]),
                "date": "2026-04-10",
                "time": "09:00",
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(create_response.status_code, 302)

        transaction = Transactions.query.filter_by(user_id=user.id, description="Groceries").first()
        self.assertIsNotNone(transaction)

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["balance"], 880.0)
        self.assertEqual(accounts["Wallet"]["transactions_delta"], -120.0)

        update_amount_response = self.client.post(
            "/transactions",
            data={
                "action": "update",
                "transaction_id": str(transaction.id),
                "description": "Groceries",
                "amount": "200",
                "currency_code": "USD",
                "type": "expense",
                "category_id": str(expense_category.id),
                "account_id": str(wallet["id"]),
                "date": "2026-04-10",
                "time": "09:00",
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(update_amount_response.status_code, 302)

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["balance"], 800.0)
        self.assertEqual(accounts["Wallet"]["transactions_delta"], -200.0)

        update_type_response = self.client.post(
            "/transactions",
            data={
                "action": "update",
                "transaction_id": str(transaction.id),
                "description": "Groceries",
                "amount": "200",
                "currency_code": "USD",
                "type": "income",
                "category_id": str(income_category.id),
                "account_id": str(wallet["id"]),
                "date": "2026-04-10",
                "time": "09:00",
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(update_type_response.status_code, 302)

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["balance"], 1200.0)
        self.assertEqual(accounts["Wallet"]["transactions_delta"], 200.0)

        move_response = self.client.post(
            "/transactions",
            data={
                "action": "update",
                "transaction_id": str(transaction.id),
                "description": "Groceries",
                "amount": "200",
                "currency_code": "USD",
                "type": "income",
                "category_id": str(income_category.id),
                "account_id": str(bank["id"]),
                "date": "2026-04-10",
                "time": "09:00",
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(move_response.status_code, 302)

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["balance"], 1000.0)
        self.assertEqual(accounts["Wallet"]["transactions_delta"], 0.0)
        self.assertEqual(accounts["Bank"]["balance"], 500.0)
        self.assertEqual(accounts["Bank"]["transactions_delta"], 200.0)

        delete_response = self.client.post(
            "/transactions",
            data={
                "action": "delete",
                "transaction_id": str(transaction.id),
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(delete_response.status_code, 302)

        accounts = self._accounts_by_name()
        self.assertEqual(accounts["Wallet"]["balance"], 1000.0)
        self.assertEqual(accounts["Bank"]["balance"], 300.0)
        self.assertEqual(accounts["Bank"]["transactions_delta"], 0.0)

    def test_deleting_account_unlinks_related_transactions(self):
        """Deleting an account keeps transaction data consistent by unlinking references."""
        user = self._create_user()
        expense_category = self._create_category(user.id, "Bills", "expense")
        self._login(user.username, "secret123")

        account = self._create_account_via_api(name="Card", initial_balance=250)

        create_response = self.client.post(
            "/transactions",
            data={
                "action": "create",
                "description": "Utility bill",
                "amount": "50",
                "currency_code": "USD",
                "type": "expense",
                "category_id": str(expense_category.id),
                "account_id": str(account["id"]),
                "date": "2026-04-12",
                "time": "18:00",
                "return_filter": "all",
            },
            follow_redirects=False,
        )
        self.assertEqual(create_response.status_code, 302)

        transaction = Transactions.query.filter_by(user_id=user.id, description="Utility bill").first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.account_id, account["id"])

        delete_account_response = self.client.delete(f"/api/accounts/{account['id']}")
        self.assertEqual(delete_account_response.status_code, 200)

        db.session.expire_all()
        transaction = db.session.get(Transactions, transaction.id)
        self.assertIsNotNone(transaction)
        self.assertIsNone(transaction.account_id)


if __name__ == "__main__":
    unittest.main()
