
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger("finance_agent")


def log_event(event: str, **fields: Any) -> None:
    """Write one structured JSON log entry."""
    record = {
        "event": event,
        "timestamp": datetime.now().astimezone().isoformat(),
        **fields,
    }
    logger.info(
        json.dumps(record, default=_json_default, separators=(",", ":"))
    )


def _json_default(value: Any):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def sanitize_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    """Log useful filter metadata without recording free-text or financial details."""
    safe_fields = {
        "snapshot_id",
        "start_date",
        "end_date",
        "as_of_date",
        "category",
        "include_transfers",
        "limit",
    }

    sanitized = {
        key: value
        for key, value in args.items()
        if key in safe_fields
    }

    # Record presence, not the actual contents, of free-text fields.
    for field in ("merchant", "fund_name"):
        if field in args:
            sanitized[f"{field}_provided"] = bool(args[field])

    return sanitized
