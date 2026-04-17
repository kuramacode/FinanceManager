import os
import sqlite3
import unittest
import uuid

from app.services.budget_services import budget_transactions_service


class FakeConverter:
    def __init__(self, rates=None):
        self.calls = []
        self.rates = rates or {}

    def convert(self, base_currency: str, target_currency: str, amount: float):
        self.calls.append((base_currency, target_currency, amount))
        rate = self.rates[(base_currency, target_currency)]
        return {"result": round(amount * rate, 2)}


class TestBudgetTransactionsService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.abspath(os.path.join("tests", ".tmp"))
        os.makedirs(self.temp_dir, exist_ok=True)
        self.db_path = os.path.join(self.temp_dir, f"budget-transactions-{uuid.uuid4().hex}.sqlite3")
        self.original_db_path = budget_transactions_service._db_path
        budget_transactions_service._db_path = lambda: self.db_path

        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency_code TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    date TEXT NOT NULL
                )
                """
            )
            db.commit()

    def tearDown(self):
        budget_transactions_service._db_path = self.original_db_path
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def _insert_transaction(self, *, user_id, amount, currency_code, tx_type, category_id, date):
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """
                INSERT INTO transactions (user_id, amount, currency_code, type, category_id, date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, amount, currency_code, tx_type, category_id, date),
            )
            db.commit()

    def test_sums_same_currency_transactions_without_conversion(self):
        self._insert_transaction(
            user_id=1,
            amount=120.50,
            currency_code="USD",
            tx_type="expense",
            category_id=10,
            date="2026-04-10",
        )
        self._insert_transaction(
            user_id=1,
            amount=29.50,
            currency_code="USD",
            tx_type="expense",
            category_id=10,
            date="2026-04-11",
        )

        converter = FakeConverter()
        result = budget_transactions_service.sum_transactions_for_budget(
            user_id=1,
            categories=[10],
            date_from="2026-04-01",
            date_to="2026-04-30",
            budget_currency_code="USD",
            converter=converter,
        )

        self.assertEqual(result, 150.0)
        self.assertEqual(converter.calls, [])

    def test_converts_mixed_currency_transactions_into_budget_currency(self):
        self._insert_transaction(
            user_id=1,
            amount=100.0,
            currency_code="UAH",
            tx_type="expense",
            category_id=7,
            date="2026-04-10",
        )
        self._insert_transaction(
            user_id=1,
            amount=10.0,
            currency_code="USD",
            tx_type="expense",
            category_id=7,
            date="2026-04-12",
        )
        self._insert_transaction(
            user_id=1,
            amount=999.0,
            currency_code="USD",
            tx_type="income",
            category_id=7,
            date="2026-04-12",
        )
        self._insert_transaction(
            user_id=1,
            amount=500.0,
            currency_code="USD",
            tx_type="expense",
            category_id=99,
            date="2026-04-12",
        )
        self._insert_transaction(
            user_id=1,
            amount=500.0,
            currency_code="USD",
            tx_type="expense",
            category_id=7,
            date="2026-05-01",
        )

        converter = FakeConverter({("USD", "UAH"): 40.0})
        result = budget_transactions_service.sum_transactions_for_budget(
            user_id=1,
            categories=[7],
            date_from="2026-04-01",
            date_to="2026-04-30",
            budget_currency_code="UAH",
            converter=converter,
        )

        self.assertEqual(result, 500.0)
        self.assertEqual(converter.calls, [("USD", "UAH", 10.0)])

    def test_includes_transactions_on_end_date_with_time_component(self):
        self._insert_transaction(
            user_id=1,
            amount=42.0,
            currency_code="UAH",
            tx_type="expense",
            category_id=3,
            date="2026-04-30 23:59:59",
        )

        result = budget_transactions_service.sum_transactions_for_budget(
            user_id=1,
            categories=[3],
            date_from="2026-04-01",
            date_to="2026-04-30",
            budget_currency_code="UAH",
            converter=FakeConverter(),
        )

        self.assertEqual(result, 42.0)


if __name__ == "__main__":
    unittest.main()
