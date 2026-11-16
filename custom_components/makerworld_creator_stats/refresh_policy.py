"""Pure scheduling rules used by the MakerWorld coordinator."""

import math

PROFILE_SECONDS = 30 * 60
EXTRA_SECONDS = 2 * 60 * 60
MAX_EXTRA_AGE = 4 * 60 * 60

EXTRA_KEYS = {
    "points": (
        "totalRegularIncome", "totalRegularExpense",
        "totalExclusiveIncome", "totalExclusiveExpense",
        "totalIncome", "totalExpense",
    ),
    "boosts": ("availableTotal", "usedTotal", "expiredTotal"),
}
FIRST_DELAY = {"points": PROFILE_SECONDS, "boosts": 2 * PROFILE_SECONDS}


def valid_timestamp(value, now, *, max_age=MAX_EXTRA_AGE):
    """Accept bounded finite epoch timestamps, rejecting booleans and future."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and now - max_age <= value <= now
    )


def due_optional(due_at, now):
    """Choose at most one due optional endpoint for this refresh."""
    ready = [kind for kind in EXTRA_KEYS if 0 < due_at.get(kind, 0) <= now]
    return min(ready, key=lambda kind: (due_at[kind], kind)) if ready else None


def first_due(now):
    """Stagger new-account requests across the next two profile polls."""
    return {kind: now + delay for kind, delay in FIRST_DELAY.items()}
