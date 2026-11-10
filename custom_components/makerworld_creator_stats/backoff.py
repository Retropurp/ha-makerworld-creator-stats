"""Small credential-free pause policy for account statistics."""

from dataclasses import dataclass
from email.utils import parsedate_to_datetime
import math

MAX_DELAY = 24 * 3600


def retry_after_seconds(value, now):
    """Accept standard seconds or HTTP-date, bounded to one day."""
    if not isinstance(value, str) or len(value) > 128:
        return 0
    value = value.strip()
    if value.isascii() and value.isdigit():
        return min(int(value), MAX_DELAY)
    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            return 0
        return max(0, min(math.ceil(date.timestamp() - now), MAX_DELAY))
    except (TypeError, ValueError, OverflowError):
        return 0


@dataclass
class Backoff:
    until: float = 0
    strikes: int = 0
    reason: str = ""

    def restore(self, saved, now):
        if saved is None:
            return
        if not isinstance(saved, dict):
            raise ValueError("Invalid pause cache")
        until, strikes, reason = (saved.get(key) for key in ("until", "strikes", "reason"))
        if (isinstance(until, bool) or not isinstance(until, (int, float))
            or not math.isfinite(until) or not 0 <= until <= now + MAX_DELAY
            or isinstance(strikes, bool) or not isinstance(strikes, int) or not 0 <= strikes <= 6
            or reason not in ("", "cloudflare", "throttled")):
            raise ValueError("Invalid pause cache")
        self.until, self.strikes, self.reason = until, strikes, reason

    def remaining(self, now):
        return max(0, self.until - now)

    def deny(self, reason, now, retry_after=0, jitter=0):
        self.strikes = min(self.strikes + 1, 6)
        base = 2 * 3600 if reason == "cloudflare" else 30 * 60
        delay = min(base * 2 ** (self.strikes - 1), 12 * 3600)
        self.until = now + min(MAX_DELAY, max(delay, retry_after) + jitter)
        self.reason = reason

    def reset(self):
        self.until, self.strikes, self.reason = 0, 0, ""

    def as_dict(self):
        return {"until": self.until, "strikes": self.strikes, "reason": self.reason}
