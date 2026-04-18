import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _resolve_db_uri() -> str:
    """Виконує логіку функції `_resolve_db_uri`."""
    raw_uri = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or ""
    ).strip()

    if not raw_uri:
        return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'users.db')}"

    if raw_uri.startswith("sqlite:///") and not raw_uri.startswith("sqlite:////"):
        sqlite_target = raw_uri.replace("sqlite:///", "", 1)
        if not os.path.isabs(sqlite_target):
            sqlite_target = os.path.join(BASE_DIR, "instance", sqlite_target)
        return f"sqlite:///{sqlite_target}"

    return raw_uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _resolve_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NBU_URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
