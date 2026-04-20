from datetime import date, datetime
from app.services.budget_services.budget_period_service import get_current_period
from app.services.budget_services.budgets_repo import (
    create_budget as repo_create_budget,
    delete_budget as repo_delete_budget,
    get_budget_by_id,
    get_budget_categories_map,
    get_budgetable_categories_by_ids,
    get_user_budgets,
    update_budget as repo_update_budget,
)
from app.services.budget_services.budget_transactions_service import BudgetConversionError, sum_transactions_for_budget
from app.services.budget_services.budget_status_service import get_budget_status


class BudgetService:
    ALLOWED_PERIOD_TYPES = {"custom", "monthly", "weekly"}

    def _parse_input_date(self, value, field_name: str, *, required: bool) -> date | None:
        """Розбирає вхідні дані у функції `_parse_input_date`."""
        if value is None or value == "":
            if required:
                raise ValueError(f"{field_name} is required")
            return None

        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value.strip()[:10])
            except ValueError as exc:
                raise ValueError(f"{field_name} must be a valid date") from exc

        raise ValueError(f"{field_name} must be a valid date")

    def _normalize_category_ids(self, category_ids) -> list[int]:
        """Нормалізує дані у функції `_normalize_category_ids`."""
        if not isinstance(category_ids, list):
            raise ValueError("Category IDs must be provided as a list")

        normalized = []
        seen = set()
        for raw_id in category_ids:
            try:
                category_id = int(raw_id)
            except (TypeError, ValueError) as exc:
                raise ValueError("Category IDs must contain only integers") from exc

            if category_id not in seen:
                seen.add(category_id)
                normalized.append(category_id)

        if not normalized:
            raise ValueError("Select at least one expense category")

        return normalized

    def _validate_payload(
        self,
        user_id,
        *,
        name,
        desc,
        amount_limit,
        currency_code,
        period_type,
        start_date,
        end_date,
        category_ids,
    ):
        """Перевіряє дані у функції `_validate_payload`."""
        name = (name or "").strip()
        if not name:
            raise ValueError("Name is required")

        desc = (desc or "").strip()

        try:
            amount_limit = float(amount_limit)
        except (TypeError, ValueError) as exc:
            raise ValueError("Amount limit must be a valid number") from exc

        if amount_limit <= 0:
            raise ValueError("Amount limit must be greater than 0")

        currency_code = (currency_code or "UAH").strip().upper()
        if len(currency_code) != 3 or not currency_code.isalpha():
            raise ValueError("Currency code must be a 3-letter code")

        period_type = (period_type or "monthly").strip().lower()
        if period_type not in self.ALLOWED_PERIOD_TYPES:
            raise ValueError("Period type must be custom, monthly, or weekly")

        start_date = self._parse_input_date(start_date, "Start date", required=True)
        if period_type == "custom":
            end_date = self._parse_input_date(end_date, "End date", required=True)
            if end_date < start_date:
                raise ValueError("End date must be on or after start date")
        else:
            end_date = start_date

        category_ids = self._normalize_category_ids(category_ids)
        valid_categories = get_budgetable_categories_by_ids(user_id, category_ids)
        if len(valid_categories) != len(category_ids):
            raise ValueError("Some selected categories are invalid or not available for budgets")

        return {
            "name": name,
            "desc": desc,
            "amount_limit": round(amount_limit, 2),
            "currency_code": currency_code,
            "period_type": period_type,
            "start_date": start_date,
            "end_date": end_date,
            "category_ids": category_ids,
        }

    def _build_budget_view(self, user_id, budget, categories):
        """Формує службові дані у функції `_build_budget_view`."""
        category_ids = [category["id"] for category in categories]
        current_period = get_current_period(budget)
        conversion_error = None

        if current_period is None:
            spent = 0.0
            period_start = budget["start_date"]
            period_end = budget["end_date"]
            status = "inactive"
        else:
            period_start, period_end = current_period
            try:
                spent = sum_transactions_for_budget(
                    user_id=user_id,
                    categories=category_ids,
                    date_from=period_start,
                    date_to=period_end,
                    budget_currency_code=budget["currency_code"],
                )
                status = get_budget_status(spent, budget["amount_limit"])
            except BudgetConversionError as exc:
                spent = 0.0
                status = "unavailable"
                conversion_error = str(exc)

        remaining = round(budget["amount_limit"] - spent, 2)
        percent = round((spent / budget["amount_limit"] * 100), 1) if budget["amount_limit"] > 0 else 0.0

        return {
            "id": budget["id"],
            "name": budget["name"],
            "desc": budget.get("desc") or "",
            "amount_limit": budget["amount_limit"],
            "currency_code": budget["currency_code"],
            "period_type": budget["period_type"],
            "start_date": budget["start_date"],
            "end_date": budget["end_date"],
            "period_start": period_start,
            "period_end": period_end,
            "category_ids": category_ids,
            "categories": categories,
            "icon": categories[0]["emoji"] if categories else budget["name"][:1].upper(),
            "spent": round(spent, 2),
            "remaining": remaining,
            "percent": percent,
            "status": status,
            "is_active": status != "inactive",
            "conversion_error": conversion_error,
        }

    def get_budgets(self, user_id):
        """Повертає дані у функції `get_budgets`."""
        budgets = get_user_budgets(user_id)
        category_map = get_budget_categories_map([budget["id"] for budget in budgets])
        return [
            self._build_budget_view(user_id, budget, category_map.get(budget["id"], []))
            for budget in budgets
        ]

    def get_budget(self, user_id, budget_id):
        """Повертає дані у функції `get_budget`."""
        budget = get_budget_by_id(budget_id, user_id)
        if budget is None:
            return None

        category_map = get_budget_categories_map([budget_id])
        return self._build_budget_view(user_id, budget, category_map.get(budget_id, []))

    def create_budget(self, user_id, *, name, desc, amount_limit, currency_code, period_type, start_date, end_date, category_ids):
        """Створює дані у функції `create_budget`."""
        payload = self._validate_payload(
            user_id,
            name=name,
            desc=desc,
            amount_limit=amount_limit,
            currency_code=currency_code,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            category_ids=category_ids,
        )
        budget = repo_create_budget(user_id=user_id, **payload)
        return self.get_budget(user_id, budget["id"])

    def update_budget(self, budget_id, user_id, *, name, desc, amount_limit, currency_code, period_type, start_date, end_date, category_ids):
        """Оновлює дані у функції `update_budget`."""
        payload = self._validate_payload(
            user_id,
            name=name,
            desc=desc,
            amount_limit=amount_limit,
            currency_code=currency_code,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            category_ids=category_ids,
        )
        budget = repo_update_budget(budget_id=budget_id, user_id=user_id, **payload)
        if budget is None:
            return None
        return self.get_budget(user_id, budget_id)

    def delete_budget(self, budget_id, user_id):
        """Видаляє дані у функції `delete_budget`."""
        return repo_delete_budget(budget_id, user_id)
