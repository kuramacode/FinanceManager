from datetime import date
import unittest

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Budget, BudgetCategory, Categories, User, db
from tests.test_support import make_test_db_uri


class TestBudgetApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
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

    def _create_category(self, user_id, name, type_="expense"):
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
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_create_budget_api_returns_computed_budget_payload(self):
        user = self._create_user()
        category = self._create_category(user.id, "Food")
        self._login(user.username, "secret123")

        response = self.client.post(
            "/api/budgets",
            json={
                "name": "Groceries",
                "desc": "Monthly essentials",
                "amount_limit": 250.0,
                "currency_code": "USD",
                "period_type": "monthly",
                "start_date": "2026-01-01",
                "end_date": "2026-01-01",
                "category_ids": [category.id],
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()

        self.assertEqual(payload["name"], "Groceries")
        self.assertEqual(payload["desc"], "Monthly essentials")
        self.assertEqual(payload["currency_code"], "USD")
        self.assertEqual(payload["category_ids"], [category.id])
        self.assertEqual(payload["categories"][0]["name"], "Food")
        self.assertEqual(payload["status"], "on_track")
        self.assertEqual(payload["spent"], 0.0)

    def test_update_and_delete_budget_api(self):
        user = self._create_user()
        first_category = self._create_category(user.id, "Food")
        second_category = self._create_category(user.id, "Dining")
        self._login(user.username, "secret123")

        create_response = self.client.post(
            "/api/budgets",
            json={
                "name": "Meals",
                "desc": "",
                "amount_limit": 400.0,
                "currency_code": "UAH",
                "period_type": "custom",
                "start_date": "2026-04-01",
                "end_date": "2026-04-30",
                "category_ids": [first_category.id],
            },
        )
        budget_id = create_response.get_json()["id"]

        update_response = self.client.put(
            f"/api/budgets/{budget_id}",
            json={
                "name": "Dining Out",
                "desc": "Restaurants and cafes",
                "amount_limit": 500.0,
                "currency_code": "UAH",
                "period_type": "custom",
                "start_date": "2026-04-01",
                "end_date": "2026-04-30",
                "category_ids": [second_category.id],
            },
        )

        self.assertEqual(update_response.status_code, 200)
        updated_payload = update_response.get_json()
        self.assertEqual(updated_payload["name"], "Dining Out")
        self.assertEqual(updated_payload["category_ids"], [second_category.id])
        self.assertEqual(updated_payload["categories"][0]["name"], "Dining")

        delete_response = self.client.delete(f"/api/budgets/{budget_id}")
        self.assertEqual(delete_response.status_code, 200)

        get_response = self.client.get("/api/budgets")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json(), [])

    def test_delete_budget_does_not_remove_another_users_links(self):
        owner = self._create_user("owner", "owner@example.com")
        intruder = self._create_user("intruder", "intruder@example.com")
        category = self._create_category(owner.id, "Rent")

        budget = Budget(
            user_id=owner.id,
            name="Housing",
            desc="",
            amount_limit=1200,
            currency_code="USD",
            period_type="custom",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
        )
        db.session.add(budget)
        db.session.commit()

        link = BudgetCategory(budget_id=budget.id, category_id=category.id)
        db.session.add(link)
        db.session.commit()

        self._login(intruder.username, "secret123")
        delete_response = self.client.delete(f"/api/budgets/{budget.id}")

        self.assertEqual(delete_response.status_code, 404)
        self.assertIsNotNone(db.session.get(Budget, budget.id))
        self.assertIsNotNone(BudgetCategory.query.filter_by(budget_id=budget.id, category_id=category.id).first())


if __name__ == "__main__":
    unittest.main()
