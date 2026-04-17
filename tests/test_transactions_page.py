from datetime import datetime
import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Accounts, Categories, Transactions, User, db


class TestTransactionsPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["SECRET_KEY"] = "test-secret"
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

    def _create_category(self, user_id, name, type_):
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

    def _create_account(self, user_id, name="Cash", currency_code="USD", status="active"):
        account = Accounts(
            name=name,
            balance=0,
            status=status,
            currency_code=currency_code,
            emoji=name[:1].upper(),
            type="cash",
            user_id=user_id,
        )
        db.session.add(account)
        db.session.commit()
        return account

    def _login(self, username="alice", password="secret123"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_get_transactions_page_renders_embedded_transaction_data(self):
        user = self._create_user()
        category = self._create_category(user.id, "Food", "expense")

        transaction = Transactions(
            amount=19.99,
            date=datetime(2026, 4, 17, 12, 30),
            description="Lunch",
            user_id=user.id,
            category_id=category.id,
            type="expense",
            currency_code="USD",
        )
        db.session.add(transaction)
        db.session.commit()

        self._login(user.username, "secret123")
        response = self.client.get("/transactions")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="transactions-data"', html)
        self.assertIn("Lunch", html)

    def test_post_create_transaction_persists_account_and_currency(self):
        user = self._create_user()
        category = self._create_category(user.id, "Food", "expense")
        account = self._create_account(user.id, name="Wallet", currency_code="EUR")

        self._login(user.username, "secret123")
        response = self.client.post(
            "/transactions",
            data={
                "action": "create",
                "description": "Lunch",
                "amount": "12.50",
                "currency_code": "EUR",
                "type": "expense",
                "category_id": str(category.id),
                "account_id": str(account.id),
                "date": "2026-04-17",
                "time": "13:45",
                "return_filter": "expense",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/transactions", response.headers["Location"])

        transaction = Transactions.query.filter_by(user_id=user.id, description="Lunch").first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.category_id, category.id)
        self.assertEqual(transaction.account_id, account.id)
        self.assertEqual(transaction.currency_code, "EUR")
        self.assertEqual(float(transaction.amount), 12.5)
        self.assertEqual(transaction.date, datetime(2026, 4, 17, 13, 45))

    def test_post_update_and_delete_transaction(self):
        user = self._create_user()
        expense_category = self._create_category(user.id, "Bills", "expense")
        income_category = self._create_category(user.id, "Salary", "income")
        account = self._create_account(user.id, name="Checking", currency_code="USD")

        transaction = Transactions(
            amount=80,
            date=datetime(2026, 4, 10, 9, 15),
            description="Old entry",
            user_id=user.id,
            category_id=expense_category.id,
            type="expense",
            account_id=account.id,
            currency_code="USD",
        )
        db.session.add(transaction)
        db.session.commit()

        self._login(user.username, "secret123")

        update_response = self.client.post(
            "/transactions",
            data={
                "action": "update",
                "transaction_id": str(transaction.id),
                "description": "Salary payout",
                "amount": "1200",
                "currency_code": "USD",
                "type": "income",
                "category_id": str(income_category.id),
                "account_id": str(account.id),
                "date": "2026-04-11",
                "time": "08:00",
                "return_filter": "income",
            },
            follow_redirects=False,
        )

        self.assertEqual(update_response.status_code, 302)

        updated = db.session.get(Transactions, transaction.id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.description, "Salary payout")
        self.assertEqual(float(updated.amount), 1200.0)
        self.assertEqual(updated.type, "income")
        self.assertEqual(updated.category_id, income_category.id)
        self.assertEqual(updated.date, datetime(2026, 4, 11, 8, 0))

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
        self.assertIsNone(db.session.get(Transactions, transaction.id))


if __name__ == "__main__":
    unittest.main()
