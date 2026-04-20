from sqlalchemy import and_, func

from app.models import db
from app.models.accounts import Accounts
from app.models.transactions import Transactions
from app.services.account_balance_service import AccountBalanceService


class AccountService:
    def _accounts_query(self, user_id):
        """Builds one centralized query with initial and current balances."""
        current_balance = AccountBalanceService.current_balance_expression()
        transactions_delta = func.coalesce(func.sum(AccountBalanceService.transaction_delta_expression()), 0)
        initial_balance = func.coalesce(Accounts.balance, 0)

        return (
            db.session.query(
                Accounts.id.label("id"),
                Accounts.name.label("name"),
                current_balance.label("balance"),
                initial_balance.label("initial_balance"),
                transactions_delta.label("transactions_delta"),
                Accounts.status.label("status"),
                Accounts.currency_code.label("currency_code"),
                Accounts.emoji.label("emoji"),
                Accounts.type.label("type"),
                Accounts.subtitle.label("subtitle"),
                Accounts.note.label("note"),
                Accounts.user_id.label("user_id"),
            )
            .outerjoin(
                Transactions,
                and_(
                    Transactions.account_id == Accounts.id,
                    Transactions.user_id == Accounts.user_id,
                ),
            )
            .filter(Accounts.user_id == user_id)
            .group_by(
                Accounts.id,
                Accounts.name,
                Accounts.balance,
                Accounts.status,
                Accounts.currency_code,
                Accounts.emoji,
                Accounts.type,
                Accounts.subtitle,
                Accounts.note,
                Accounts.user_id,
            )
            .order_by(Accounts.name.asc(), Accounts.id.asc())
        )

    @staticmethod
    def _serialize_account(row) -> dict:
        """Normalizes an aggregated account row for templates and APIs."""
        return {
            "id": int(row.id),
            "name": row.name,
            "balance": round(float(row.balance or 0.0), 2),
            "initial_balance": round(float(row.initial_balance or 0.0), 2),
            "transactions_delta": round(float(row.transactions_delta or 0.0), 2),
            "status": row.status,
            "currency_code": row.currency_code,
            "emoji": row.emoji,
            "type": row.type,
            "subtitle": row.subtitle or "",
            "note": row.note or "",
            "user_id": int(row.user_id),
        }

    def get_accounts(self, user_id):
        """Returns accounts with balances derived from linked transactions."""
        rows = self._accounts_query(user_id).all()
        return [self._serialize_account(row) for row in rows]

    def get_account(self, user_id, account_id):
        """Returns one account with its computed current balance."""
        row = self._accounts_query(user_id).filter(Accounts.id == account_id).first()
        if row is None:
            return None
        return self._serialize_account(row)

    def create_account(self, user_id, name, initial_balance, status, currency_code, emoji, type, subtitle, note):
        """Creates an account storing only the initial balance persistently."""
        account = Accounts(
            user_id=user_id,
            name=name,
            balance=round(float(initial_balance or 0.0), 2),
            status=status,
            currency_code=currency_code,
            emoji=emoji,
            type=type,
            subtitle=subtitle,
            note=note,
        )
        db.session.add(account)
        db.session.commit()
        return self.get_account(user_id, account.id)

    def update_account(self, id_, user_id, name, initial_balance, status, currency_code, emoji, type, subtitle, note):
        """Updates account metadata and its initial balance."""
        account = Accounts.query.filter_by(id=id_, user_id=user_id).first()
        if account is None:
            return None

        account.name = name
        account.balance = round(float(initial_balance or 0.0), 2)
        account.status = status
        account.currency_code = currency_code
        account.emoji = emoji
        account.type = type
        account.subtitle = subtitle
        account.note = note
        db.session.commit()
        return self.get_account(user_id, id_)

    def delete_account(self, id_, user_id):
        """Deletes an account and unlinks its transactions."""
        account = Accounts.query.filter_by(id=id_, user_id=user_id).first()
        if account is None:
            return False

        Transactions.query.filter_by(user_id=user_id, account_id=id_).update(
            {Transactions.account_id: None},
            synchronize_session=False,
        )
        db.session.delete(account)
        db.session.commit()
        return True
