import tempfile
import uuid
from pathlib import Path


def make_test_db_uri() -> str:
    """Виконує допоміжну тестову дію `make_test_db_uri`."""
    test_dir = Path(tempfile.gettempdir()) / "finance-manager-tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_db = test_dir / f"finance-manager-test-{uuid.uuid4().hex}.sqlite3"
    return f"sqlite:///{test_db.resolve()}"
