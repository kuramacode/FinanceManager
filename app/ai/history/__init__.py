"""Lightweight AI run history hooks.

The project does not currently have a persistent AI history table. This module
keeps a bounded in-process audit trail so use cases can record status, errors,
and results through the existing history package without coupling execution to
Flask routes or UI code.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


_RUNS: deque[dict[str, Any]] = deque(maxlen=100)


def record_ai_run(
    *,
    action_id: str,
    page_key: str,
    user_id: int,
    status: str,
    error: str | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "action_id": action_id,
        "page_key": page_key,
        "user_id": user_id,
        "status": status,
        "error": error,
        "result": deepcopy(result or {}),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    _RUNS.append(entry)
    return deepcopy(entry)


def get_recent_ai_runs(limit: int = 20) -> list[dict[str, Any]]:
    return [deepcopy(item) for item in list(_RUNS)[-limit:]]
