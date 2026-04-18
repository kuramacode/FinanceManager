from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from flask import current_app, has_app_context

from app.config import BASE_DIR, Config


def default_sqlite_path() -> Path:
    return (Path(BASE_DIR) / "instance" / "users.db").resolve()


def current_database_uri() -> str:
    if has_app_context():
        return str(current_app.config.get("SQLALCHEMY_DATABASE_URI") or "").strip()
    return str(Config.SQLALCHEMY_DATABASE_URI).strip()


def sqlite_path_from_uri(database_uri: str | None = None) -> Path:
    uri = (database_uri or current_database_uri()).strip()
    if uri == "sqlite:///:memory:":
        raise ValueError("In-memory SQLite cannot be used with direct sqlite3 file connections.")
    if not uri.startswith("sqlite:///"):
        raise ValueError(f"Unsupported database URI for sqlite3 access: {uri!r}")

    raw_path = uri.replace("sqlite:///", "", 1)
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path(BASE_DIR) / "instance" / raw_path
    return path.resolve()


def sqlite_db_path(database_uri: str | None = None) -> str:
    return str(sqlite_path_from_uri(database_uri))


def sqlite_uri_for_path(path: str | Path) -> str:
    return f"sqlite:///{Path(path).resolve()}"


def ensure_sqlite_directory(database_uri: str | None = None) -> Path | None:
    uri = (database_uri or current_database_uri()).strip()
    if not uri.startswith("sqlite:///") or uri == "sqlite:///:memory:":
        return None

    path = sqlite_path_from_uri(uri)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def make_test_database_uri() -> str:
    test_dir = Path(tempfile.gettempdir()) / "finance-manager-tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_db_path = test_dir / f"finance-manager-{uuid.uuid4().hex}.sqlite3"
    return sqlite_uri_for_path(test_db_path)
