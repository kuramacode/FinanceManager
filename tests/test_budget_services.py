from datetime import date
import unittest
from unittest.mock import patch

from app.services.budget_services.budget_period_service import get_current_period
from app.services.budget_services.budget_status_service import get_budget_status
from app.services.budget_services.budget_transactions_service import BudgetConversionError
from app.services.budget_services.budgets import BudgetService


class TestBudgetPeriodService(unittest.TestCase):
    def test_custom_period_accepts_string_dates(self):
        """Перевіряє сценарій `custom_period_accepts_string_dates`."""
        budget = {
            "period_type": "custom",
            "start_date": "2026-04-01",
            "end_date": "2026-04-30",
        }

        start_date, end_date = get_current_period(budget)

        self.assertEqual(start_date, date(2026, 4, 1))
        self.assertEqual(end_date, date(2026, 4, 30))


class TestBudgetStatusService(unittest.TestCase):
    def test_returns_on_track_for_safe_budget_usage(self):
        """Перевіряє сценарій `returns_on_track_for_safe_budget_usage`."""
        self.assertEqual(get_budget_status(25, 100), "on_track")

    def test_returns_warning_when_budget_reaches_80_percent(self):
        """Перевіряє сценарій `returns_warning_when_budget_reaches_80_percent`."""
        self.assertEqual(get_budget_status(80, 100), "warning")

    def test_returns_invalid_for_non_positive_limit(self):
        """Перевіряє сценарій `returns_invalid_for_non_positive_limit`."""
        self.assertEqual(get_budget_status(10, 0), "invalid")


class TestBudgetService(unittest.TestCase):
    @patch("app.services.budget_services.budgets.sum_transactions_for_budget")
    @patch("app.services.budget_services.budgets.get_budget_categories_map")
    @patch("app.services.budget_services.budgets.get_user_budgets")
    def test_uses_current_period_for_monthly_budget(
        self,
        mock_get_user_budgets,
        mock_get_budget_categories_map,
        mock_sum_transactions,
    ):
        """Перевіряє сценарій `uses_current_period_for_monthly_budget`."""
        mock_get_user_budgets.return_value = [
            {
                "id": 1,
                "name": "Food",
                "amount_limit": 1000.0,
                "currency_code": "UAH",
                "period_type": "monthly",
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 1, 31),
            }
        ]
        mock_get_budget_categories_map.return_value = {
            1: [
                {"id": 10, "name": "Food", "emoji": "F", "type": "expense", "built_in": False},
                {"id": 11, "name": "Dining", "emoji": "D", "type": "expense", "built_in": False},
            ]
        }
        mock_sum_transactions.return_value = 250.0

        with patch("app.services.budget_services.budget_period_service._today", return_value=date(2026, 4, 17)):
            budgets = BudgetService().get_budgets(user_id=7)

        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0]["period_start"], date(2026, 4, 1))
        self.assertEqual(budgets[0]["period_end"], date(2026, 4, 30))
        self.assertEqual(budgets[0]["spent"], 250.0)
        self.assertEqual(budgets[0]["status"], "on_track")
        self.assertEqual(budgets[0]["category_ids"], [10, 11])
        self.assertEqual(budgets[0]["icon"], "F")
        mock_sum_transactions.assert_called_once_with(
            user_id=7,
            categories=[10, 11],
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
            budget_currency_code="UAH",
        )

    @patch("app.services.budget_services.budgets.sum_transactions_for_budget")
    @patch("app.services.budget_services.budgets.get_budget_categories_map")
    @patch("app.services.budget_services.budgets.get_user_budgets")
    def test_marks_future_budget_as_inactive_without_querying_transactions(
        self,
        mock_get_user_budgets,
        mock_get_budget_categories_map,
        mock_sum_transactions,
    ):
        """Перевіряє сценарій `marks_future_budget_as_inactive_without_querying_transactions`."""
        mock_get_user_budgets.return_value = [
            {
                "id": 2,
                "name": "Travel",
                "amount_limit": 500.0,
                "currency_code": "USD",
                "period_type": "custom",
                "start_date": date(2026, 5, 1),
                "end_date": date(2026, 5, 31),
            }
        ]
        mock_get_budget_categories_map.return_value = {
            2: [{"id": 15, "name": "Travel", "emoji": "T", "type": "expense", "built_in": False}]
        }

        with patch("app.services.budget_services.budget_period_service._today", return_value=date(2026, 4, 17)):
            budgets = BudgetService().get_budgets(user_id=7)

        self.assertEqual(budgets[0]["status"], "inactive")
        self.assertEqual(budgets[0]["spent"], 0.0)
        mock_sum_transactions.assert_not_called()

    @patch("app.services.budget_services.budgets.sum_transactions_for_budget")
    @patch("app.services.budget_services.budgets.get_budget_categories_map")
    @patch("app.services.budget_services.budgets.get_user_budgets")
    def test_conversion_failure_does_not_crash_budget_list(
        self,
        mock_get_user_budgets,
        mock_get_budget_categories_map,
        mock_sum_transactions,
    ):
        """Перевіряє сценарій `conversion_failure_does_not_crash_budget_list`."""
        mock_get_user_budgets.return_value = [
            {
                "id": 3,
                "name": "Shopping",
                "amount_limit": 300.0,
                "currency_code": "EUR",
                "period_type": "custom",
                "start_date": date(2026, 4, 1),
                "end_date": date(2026, 4, 30),
            }
        ]
        mock_get_budget_categories_map.return_value = {
            3: [{"id": 22, "name": "Shopping", "emoji": "S", "type": "expense", "built_in": False}]
        }
        mock_sum_transactions.side_effect = BudgetConversionError("Failed to convert USD to EUR")

        budgets = BudgetService().get_budgets(user_id=9)

        self.assertEqual(budgets[0]["status"], "unavailable")
        self.assertEqual(budgets[0]["spent"], 0.0)
        self.assertEqual(budgets[0]["conversion_error"], "Failed to convert USD to EUR")

    @patch.object(BudgetService, "get_budget")
    @patch("app.services.budget_services.budgets.repo_create_budget")
    @patch("app.services.budget_services.budgets.get_budgetable_categories_by_ids")
    def test_create_budget_normalizes_payload_before_persisting(
        self,
        mock_get_budgetable_categories_by_ids,
        mock_repo_create_budget,
        mock_get_budget,
    ):
        """Перевіряє сценарій `create_budget_normalizes_payload_before_persisting`."""
        mock_get_budgetable_categories_by_ids.return_value = [
            {"id": 5, "name": "Food", "emoji": "F", "type": "expense", "built_in": False}
        ]
        mock_repo_create_budget.return_value = {"id": 44}
        mock_get_budget.return_value = {"id": 44, "name": "Food"}

        result = BudgetService().create_budget(
            3,
            name=" Food ",
            desc=" Monthly groceries ",
            amount_limit="1500.55",
            currency_code="usd",
            period_type="weekly",
            start_date="2026-04-17",
            end_date="",
            category_ids=["5", "5"],
        )

        self.assertEqual(result, {"id": 44, "name": "Food"})
        mock_repo_create_budget.assert_called_once()
        _, kwargs = mock_repo_create_budget.call_args
        self.assertEqual(kwargs["user_id"], 3)
        self.assertEqual(kwargs["name"], "Food")
        self.assertEqual(kwargs["desc"], "Monthly groceries")
        self.assertEqual(kwargs["amount_limit"], 1500.55)
        self.assertEqual(kwargs["currency_code"], "USD")
        self.assertEqual(kwargs["period_type"], "weekly")
        self.assertEqual(kwargs["start_date"], date(2026, 4, 17))
        self.assertEqual(kwargs["end_date"], date(2026, 4, 17))
        self.assertEqual(kwargs["category_ids"], [5])


if __name__ == "__main__":
    unittest.main()
