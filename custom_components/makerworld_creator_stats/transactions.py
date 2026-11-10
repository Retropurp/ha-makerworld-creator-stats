"""Validate and aggregate dated point-income transactions."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

DAY = 86400
HISTORY_INTERVAL = 6 * 3600


def read_cache(saved, now):
    """Validate the small, credential-free local transaction cache."""
    if not isinstance(saved, dict):
        return None
    synced_at = float(signed_number(saved.get("synced_at")))
    if not 0 < synced_at <= now:
        return None
    events = saved.get("events")
    if not isinstance(events, list) or len(events) > 5000:
        return None
    normalized = []
    for event in events:
        if not isinstance(event, dict):
            return None
        timestamp = signed_number(event.get("time"))
        if timestamp < 0 or timestamp > now:
            return None
        parsed = {"time": float(timestamp)}
        for key in ("regular", "exclusive", "combined"):
            value = signed_number(event[key]) if event.get(key) is not None else None
            if value is not None and value < 0:
                return None
            parsed[key] = str(value) if value is not None else None
        if event.get("combined") is None:
            return None
        normalized.append(parsed)
    return synced_at, normalized


class TransactionError(ValueError):
    """A history response was incomplete or cannot be interpreted safely."""


def signed_number(value):
    if value is None or isinstance(value, bool):
        raise TransactionError("Missing transaction amount")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise TransactionError("Invalid transaction amount") from None
    if not result.is_finite():
        raise TransactionError("Invalid transaction amount")
    return result


def parse_transaction(row):
    if not isinstance(row, dict):
        raise TransactionError("Unexpected transaction format")
    try:
        timestamp = datetime.fromisoformat(row["pointTime"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError
        timestamp = timestamp.timestamp()
    except (KeyError, TypeError, AttributeError, ValueError, OverflowError):
        raise TransactionError("Missing or invalid transaction timestamp") from None
    total = signed_number(row.get("pointChange"))
    result = {"time": timestamp, "combined": str(max(total, Decimal(0)))}
    for key, field in (("regular", "pointChangeRegular"), ("exclusive", "pointChangeExclusive")):
        value = row.get(field)
        # An absent split remains unknown. Expenses contribute no earned points.
        result[key] = str(max(signed_number(value), Decimal(0))) if value is not None else None
        if total <= 0:
            result[key] = "0"
    return result


def income_in_window(events, key, days, now):
    total = Decimal(0)
    cutoff = now - days * DAY
    for event in events:
        if cutoff < event["time"] <= now:
            value = event.get(key)
            if value is None:
                return None
            total += signed_number(value)
    return total
