import sqlite3
from app.utils.main_scripts import _db_path

class AccountService:
    def get_accounts(self, user_id):
        """Повертає дані у функції `get_accounts`."""
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            rows = cur.execute('''
                               SELECT id, name, balance, status, currency_code, emoji, type, subtitle, note FROM accounts
                               WHERE user_id=?
                               ''', (user_id, )).fetchall()
            
            return [
                dict(row)
                for row in rows
            ]
            
    def create_account(self, user_id, name, initial_balance, status, currency_code, emoji, type, subtitle, note):
        """Створює дані у функції `create_account`."""
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            # FIX: removed trailing comma after last column, fixed parameter order
            # (was: name, balance, status, currency_code, user_id, emoji — user_id/emoji swapped)
            cur.execute('''
                        INSERT INTO accounts (name, balance, status, currency_code, emoji, type, subtitle, note, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (name, initial_balance, status, currency_code, emoji, type, subtitle, note, user_id, ))
            db.commit()
            
            row = cur.execute('''
                              SELECT id, name, balance, status, currency_code, emoji, type, subtitle, note, user_id FROM accounts
                              WHERE id=?
                              ''', (cur.lastrowid, )).fetchone()
            return dict(row)
        
    def update_account(self, id_, user_id, name, balance, status, currency_code, emoji, type, subtitle, note):
        """Оновлює дані у функції `update_account`."""
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            existing = cur.execute('''
                                   SELECT id FROM accounts
                                   WHERE user_id=? AND id=?
                                   ''', (user_id, id_,)).fetchall()
            
            if not existing:
                return None
            
            cur.execute('''
                        UPDATE accounts
                        SET name=?, balance=?, status=?, currency_code=?, emoji=?, type=?, subtitle=?, note=?
                        WHERE id=? AND user_id=?
                        ''', (name, balance, status, currency_code, emoji, type, subtitle, note, id_, user_id, ))
            db.commit()
            
            row = cur.execute('''
                              SELECT id, name, balance, status, currency_code, emoji, type, subtitle, note, user_id FROM accounts
                              WHERE id=?
                              ''', (id_, )).fetchone()
            
            return dict(row)
        
    def delete_account(self, id_, user_id):
        """Видаляє дані у функції `delete_account`."""
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            result = cur.execute('''
                                 DELETE FROM accounts WHERE id=? AND user_id=?
                                 ''', (id_, user_id,))
            db.commit()
            
        return result.rowcount > 0
