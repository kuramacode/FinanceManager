import sqlite3
from app.utils.main_scripts import _db_path


def _is_built_in_db_value(value) -> bool:
    return str(value).strip().lower() in {"1", "true"}


class Category_Service:
    def get_categories(self, user_id):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()

            rows = cur.execute(
                """
                SELECT id, name, desc, user_id, emoji, built_in, type
                FROM categories
                WHERE user_id = ?
                   OR CAST(COALESCE(built_in, 0) AS TEXT) IN ('1', 'True', 'true')
                ORDER BY built_in DESC, name ASC
                """,
                (user_id,),
            ).fetchall()

            return [
                {
                    **dict(row),
                    "built_in": _is_built_in_db_value(dict(row).get("built_in"))
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
                        ''', (name, desc, user_id, emoji, False, type_,))
            db.commit()
             
            row = cur.execute('''
                              SELECT id, name, desc, user_id, emoji, built_in, type FROM categories WHERE id=?
                              ''', (cur.lastrowid, )).fetchone()
             
            return {
                **dict(row),
                "built_in": _is_built_in_db_value(dict(row).get("built_in"))
                }
        
    def update_category(self, category_id, user_id, name, desc, emoji, type_):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
            # Only allow editing user-owned (non built-in) categories
            existing = cur.execute('''
                                   SELECT id FROM categories
                                   WHERE id=? AND user_id=?
                                     AND CAST(COALESCE(built_in, 0) AS TEXT) NOT IN ('1', 'True', 'true')
                                   ''', (category_id, user_id,)).fetchone()
             
            if not existing:
                return None
            
            cur.execute('''
                        UPDATE categories
                        SET name=?, desc=?, emoji=?, type=?
                        WHERE id=? AND user_id=?
                          AND CAST(COALESCE(built_in, 0) AS TEXT) NOT IN ('1', 'True', 'true')
                        ''', (name, desc, emoji, type_, category_id, user_id,))
            db.commit()
            
            row = cur.execute('''
                              SELECT id, name, desc, user_id, emoji, built_in, type FROM categories
                              WHERE id=?
                              ''', (category_id, )).fetchone()
            
            return {
                **dict(row),
                "built_in": _is_built_in_db_value(dict(row).get("built_in"))
                }
            
    def delete_category(self, category_id, user_id):
        with sqlite3.connect(_db_path()) as db:
            db.row_factory = sqlite3.Row
            cur = db.cursor()
             
            result = cur.execute('''
                                 DELETE FROM categories
                                 WHERE id=? AND user_id=?
                                   AND CAST(COALESCE(built_in, 0) AS TEXT) NOT IN ('1', 'True', 'true')
                                 ''', (category_id, user_id,))
            db.commit()
             
            return result.rowcount > 0
