import sqlite3
from app.utils.main_scripts import _db_path


class Category_Service:
    def get_categories(self, user_id):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()

            rows = cur.execute(
                """
                SELECT id, name, desc, user_id, emoji, built_in, type
                FROM categories
                WHERE built_in = ? OR user_id = ?
                ORDER BY built_in DESC, name ASC
                """,
                ("True", user_id),
            ).fetchall()

            return [
                {
                    **dict(row),
                    "built_in": dict(row)["built_in"] == "True"
                }
                for row in rows
            ]
        
    def create_category(self, user_id, name, desc, emoji, type_):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            cur.execute('''
                        INSERT INTO categories (name, desc, user_id, emoji, built_in, type)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (name, desc, user_id, emoji, "False", type_,))
            db.commit()
            
            row = cur.execute('''
                              SELECT id, name, desc, user_id, emoji, built_in, type FROM categories WHERE id=?
                              ''', (cur.lastrowid, )).fetchone()
            
            return {
                **dict(row),
                "built_in": dict(row)["built_in"] == "True"
                }
        
    def update_category(self, category_id, user_id, name, desc, emoji, type_):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            # Only allow editing user-owned (non built-in) categories
            existing = cur.execute('''
                                   SELECT id FROM categories WHERE id=? AND user_id=? AND built_in=?
                                   ''', (category_id, user_id, "False",)).fetchone()
            
            if not existing:
                return None
            
            cur.execute('''
                        UPDATE categories
                        SET name=?, desc=?, emoji=?, type=?
                        WHERE id=? AND user_id=? AND built_in=?
                        ''', (name, desc, emoji, type_, category_id, user_id, "False",))
            db.commit()
            
            row = cur.execute('''
                              SELECT id, name, desc, user_id, emoji, built_in, type FROM categories
                              WHERE id=?
                              ''', (category_id, )).fetchone()
            
            return {
                **dict(row),
                "built_in": dict(row)["built_in"] == "True"
                }
            
    def delete_category(self, category_id, user_id):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            
            result = cur.execute('''
                                 DELETE FROM categories WHERE id=? AND user_id=? AND built_in=?
                                 ''', (category_id, user_id, "False",))
            db.commit()
            
            return result.rowcount > 0