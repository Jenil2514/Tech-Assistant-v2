import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config.settings import settings


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _audit_path() -> Path:
    return Path(settings.PROVISIONING_AUDIT_LOG_PATH)


def append_audit_event(
    event_type: str,
    request_id: str,
    actor_id: str | None,
    details: dict[str, Any] | None = None,
) -> None:
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": _utc_now(),
        "event_type": event_type,
        "request_id": request_id,
        "actor_id": actor_id,
        "details": details or {},
    }

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, sort_keys=True) + "\n")
