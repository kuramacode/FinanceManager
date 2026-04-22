from __future__ import annotations

from sqlalchemy import case, func

from app.models.accounts import Accounts
from app.models.transactions import Transactions


class AccountBalanceService:
    """Centralizes account balance calculations derived from transactions."""

    @staticmethod
    def _normalized_amount_expr():
        return func.abs(func.coalesce(Transactions.amount, 0))

    @classmethod
    def transaction_delta_expression(cls):
        """Builds the SQL expression for transaction impact on account balance."""
        amount = cls._normalized_amount_expr()
        return case(
            (Transactions.type == "income", amount),
            (Transactions.type.in_(("expense", "transfer")), -amount),
            else_=0.0,
        )

    @staticmethod
    def transaction_delta(transaction_type: str | None, amount) -> float:
        """Returns the signed balance impact for a single transaction."""
        normalized_type = str(transaction_type or "").strip().lower()
        normalized_amount = abs(float(amount or 0.0))

        if normalized_type == "income":
            return normalized_amount
        if normalized_type in {"expense", "transfer"}:
            return -normalized_amount
        return 0.0

    @classmethod
    def current_balance_expression(cls):
        """Builds the SQL expression for current account balance."""
        initial_balance = func.coalesce(Accounts.balance, 0)
        transactions_delta = func.coalesce(func.sum(cls.transaction_delta_expression()), 0)
        return initial_balance + transactions_delta
