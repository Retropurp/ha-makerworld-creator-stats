"""Coordinated, rate-conscious MakerWorld account polling."""

from asyncio import Lock
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import logging
import random
import time

from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, AuthError
from .backoff import Backoff
from .const import BOOSTS, DOMAIN, POINTS
from .errors import AccessDeniedError, CloudflareError, RateLimitError
from .profile import MakerWorldProfile, as_number
from .refresh_policy import (
    EXTRA_KEYS, EXTRA_SECONDS, PROFILE_SECONDS, MAX_EXTRA_AGE,
    due_optional, first_due, valid_timestamp,
)

LOGGER = logging.getLogger(__name__)
STORAGE_ERRORS = (HomeAssistantError, OSError, ValueError, TypeError, OverflowError, KeyError)
OPTIONAL_AUTH_DELAY = 6 * 3600
PROFILE_ERROR_DELAY = 2 * 3600


class ScheduledUpdateFailed(UpdateFailed):
    """Expose the retry time on HA versions that support it."""

    def __init__(self, message, *, retry_after):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class AccountRefresh:
    """Entry-wide refresh state shared across coordinator reloads."""

    lock: Lock = field(default_factory=Lock)
    data: dict | None = None
    success_at: float = 0
    due_at: float = 0
    retry_at: float = 0
    error: str = ""
    extras_loaded: bool = False
    extras: dict = field(default_factory=lambda: {kind: {} for kind in EXTRA_KEYS})
    extra_updated: dict = field(default_factory=lambda: {kind: 0.0 for kind in EXTRA_KEYS})
    extra_due: dict = field(default_factory=lambda: {kind: 0.0 for kind in EXTRA_KEYS})
    extra_error: dict = field(default_factory=lambda: {kind: "" for kind in EXTRA_KEYS})
    rejected_private: dict = field(default_factory=dict)


class MakerWorldCoordinator(DataUpdateCoordinator[MakerWorldProfile]):
    """One creator profile per hour, at most one optional GET per refresh."""

    def __init__(self, hass, entry, api):
        super().__init__(
            hass, LOGGER, name=DOMAIN, config_entry=entry,
            update_interval=self._profile_interval(),
        )
        self.api = api
        # An opaque token fingerprint (never the token itself) ties 401 refusals
        # to a specific login, including across HA restarts.
        self._token_fingerprint = sha256(api.token.encode("utf-8")).hexdigest()
        # Legacy entries retain private stats; new entries require opt-in.
        self._private_stats_enabled = bool(entry.options.get(
            "private_stats_enabled", entry.data.get("private_stats_enabled", True)
        ))
        self._previous_refresh_failed = False
        self._first_profile_pending = True
        self.account_id = entry.unique_id
        self.income_events = None
        self.history_synced_at = 0
        self.history_error = "Historical transaction import disabled in this beta"
        self.history_persisted = True
        self.reward_options = dict(entry.options)

        shared = hass.data.setdefault(DOMAIN, {})
        refreshes = shared.setdefault("refreshes", {})
        if entry.entry_id not in refreshes:
            refreshes[entry.entry_id] = AccountRefresh()
        self.refresh = refreshes[entry.entry_id]
        self.pause = shared.setdefault("pauses", {}).setdefault(
            entry.entry_id, {
                "state": Backoff(), "loaded": False, "persisted": True, "endpoint": "profile",
            },
        )
        self.pause_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.pause")

        self.extras_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.extras")
        self._extras = self.refresh.extras
        self._extra_updated = self.refresh.extra_updated
        self._due = self.refresh.extra_due
        self.extra_error = self.refresh.extra_error
        self._rejected_private = self.refresh.rejected_private

        self.last_profile_success = 0.0
        self.next_profile_at = 0.0
        self.last_error = ""
        self.connection_status = "initializing"

    @staticmethod
    def _profile_interval():
        return timedelta(seconds=PROFILE_SECONDS + random.uniform(0, 60))

    async def _async_setup(self):
        async with self.refresh.lock:
            await self._async_load_refresh_state()

    async def _async_load_refresh_state(self):
        if not self.pause["loaded"]:
            try:
                saved = await self.pause_store.async_load()
                now = time.time()
                self.pause["state"].restore(saved, now)
                retry_at = saved.get("profile_retry_at") if saved else None
                if valid_timestamp(retry_at, now + PROFILE_ERROR_DELAY, max_age=PROFILE_ERROR_DELAY):
                    self.refresh.retry_at = retry_at
                if saved and saved.get("endpoint") in ("points", "boosts"):
                    self.pause["endpoint"] = saved["endpoint"]
            except STORAGE_ERRORS:
                raise ScheduledUpdateFailed(
                    "Could not read saved protection pause. Request skipped.",
                    retry_after=3600,
                ) from None
            self.pause["loaded"] = True

        now = time.time()
        if not self.refresh.extras_loaded:
            self._due.update(first_due(now))
            try:
                cache = await self.extras_store.async_load()
            except STORAGE_ERRORS:
                cache = None
            if isinstance(cache, dict) and cache.get("account_id") == self.account_id:
                rejected = cache.get("rejected_private", {})
                if isinstance(rejected, dict):
                    for kind in EXTRA_KEYS:
                        if rejected.get(kind) == self._token_fingerprint:
                            self._rejected_private[kind] = self._token_fingerprint
                for kind in EXTRA_KEYS:
                    stored = cache.get(kind)
                    if not isinstance(stored, dict):
                        continue
                    stamp = stored.get("updated_at")
                    values = stored.get("values")
                    due = stored.get("due_at")
                    valid_due = valid_timestamp(due, now + OPTIONAL_AUTH_DELAY, max_age=OPTIONAL_AUTH_DELAY)
                    if valid_due:
                        self._due[kind] = due
                    if not valid_timestamp(stamp, now) or not isinstance(values, dict):
                        continue
                    clean = self._clean_values(kind, values)
                    if clean:
                        self._extras[kind] = clean
                        self._extra_updated[kind] = float(stamp)
                        self._due[kind] = max(due if valid_due else now, float(stamp) + EXTRA_SECONDS)
            self.refresh.extras_loaded = True

        for kind in EXTRA_KEYS:
            if self._rejected_private.get(kind) != self._token_fingerprint:
                self._rejected_private.pop(kind, None)
                if not self._due.get(kind):
                    self._due[kind] = first_due(now)[kind]
            if not self._private_stats_enabled or kind in self._rejected_private:
                self._due[kind] = 0

        remaining = self.pause["state"].remaining(now)
        if remaining:
            self.connection_status = "paused"
            self.next_profile_at = self.pause["state"].until

    @staticmethod
    def _clean_values(kind, data):
        """Store only documented numeric counters, never raw API payloads."""
        if not isinstance(data, dict):
            return {}
        clean = {}
        for key in EXTRA_KEYS[kind]:
            value = as_number(data.get(key))
            if value is not None and value >= 0:
                clean[key] = value
        return clean

    async def _save_extras(self):
        payload = {"account_id": self.account_id, "rejected_private": self._rejected_private.copy()}
        for kind in EXTRA_KEYS:
            payload[kind] = {
                "updated_at": self._extra_updated[kind],
                "due_at": self._due[kind],
                "values": self._extras[kind],
            }
        try:
            await self.extras_store.async_save(payload)
        except STORAGE_ERRORS:
            LOGGER.warning("Could not persist MakerWorld optional-statistics cache")

    def _current_extra(self, kind, now):
        if not self._private_stats_enabled:
            return {}
        if valid_timestamp(self._extra_updated[kind], now, max_age=MAX_EXTRA_AGE):
            return self._extras[kind]
        return {}

    @property
    def next_points_at(self):
        return self._next_optional_time("points")

    @property
    def next_boosts_at(self):
        return self._next_optional_time("boosts")

    def _next_optional_time(self, kind):
        if not self._private_stats_enabled or kind in self._rejected_private:
            return None
        due = self._due[kind]
        if not due:
            return None
        if self.connection_status == "auth_required":
            return None
        return max(due, self.next_profile_update or 0)

    @property
    def next_profile_update(self):
        remaining = self.pause["state"].remaining(time.time())
        if remaining:
            return max(self.next_profile_at, self.pause["state"].until)
        return self.next_profile_at or None

    async def async_request_refresh(self):
        """Keep manual entity refreshes within the scheduled request budget."""
        if self.connection_status == "auth_required" or time.time() < self.next_profile_at:
            return
        await super().async_request_refresh()

    async def _async_update_data(self):
        async with self.refresh.lock:
            return await self._async_update_account()

    async def _async_update_account(self):
        now = time.time()
        refresh = self.refresh
        self.last_profile_success = refresh.success_at
        remaining = self.pause["state"].remaining(now)
        if remaining:
            self.connection_status = "paused"
            self.next_profile_at = self.pause["state"].until
            raise self._pause_failure(remaining)
        if now < refresh.retry_at:
            raise self._profile_failure(now)
        if refresh.data is not None and now < refresh.due_at:
            self.next_profile_at = refresh.due_at
            self.update_interval = timedelta(seconds=refresh.due_at - now)
            failed_detail = next((error for error in self.extra_error.values() if error), "")
            self.connection_status = "partial" if failed_detail else "success"
            self.last_error = failed_detail
            self._first_profile_pending = False
            return self._profile_with_extras(refresh.data, now)

        try:
            raw_profile = await self.api.profile()
            if str(raw_profile.get("uid")) != self.account_id:
                raise AuthError("MakerWorld account changed; sign in again")
            # Validate the profile before recording success or calling an optional endpoint.
            MakerWorldProfile.from_json(raw_profile)
        except AuthError as error:
            refresh.data = None
            self.connection_status = "auth_required"
            self.last_error = str(error)
            self.next_profile_at = 0
            raise ConfigEntryAuthFailed("Please sign in with a new email code") from None
        except (CloudflareError, RateLimitError, AccessDeniedError) as error:
            self.last_error = str(error)
            raise await self._async_pause(error, "profile") from None
        except ApiError as error:
            raise await self._async_profile_failure(str(error)) from None
        except (AttributeError, TypeError, ValueError):
            raise await self._async_profile_failure("Unexpected profile format") from None

        now = time.time()
        refresh.data = raw_profile
        refresh.success_at = self.last_profile_success = now
        refresh.retry_at = 0
        self.update_interval = self._profile_interval()
        refresh.due_at = self.next_profile_at = now + self.update_interval.total_seconds()
        self.connection_status = "success"
        self.last_error = ""

        # A setup without an in-memory snapshot starts with the profile only.
        # Reloads with a snapshot do not make a request during setup.
        chosen = None if self._first_profile_pending else due_optional(self._due, now)
        self._first_profile_pending = False
        if chosen is not None:
            await self._refresh_optional(chosen)

        if not self.pause["state"].remaining(time.time()):
            if any(self.extra_error.values()):
                # A healthy profile does not imply optional endpoints succeeded.
                self.connection_status = "partial"
            if self.pause["state"].strikes and self.pause["endpoint"] == "profile":
                self.pause["state"].reset()
                await self._save_pause()
            refresh.due_at = self.next_profile_at = time.time() + self.update_interval.total_seconds()

        return self._profile_with_extras(raw_profile, time.time())

    def _profile_with_extras(self, raw_profile, now):
        return MakerWorldProfile.from_json(
            raw_profile, self._current_extra("points", now),
            self._current_extra("boosts", now),
        )

    async def _async_profile_failure(self, message):
        refresh = self.refresh
        refresh.data = None
        refresh.error = message
        refresh.retry_at = time.time() + PROFILE_ERROR_DELAY
        await self._save_pause()
        return self._profile_failure(time.time())

    def _profile_failure(self, now):
        refresh = self.refresh
        self.connection_status = "error"
        self.last_error = refresh.error or "Waiting to retry the MakerWorld profile"
        self.next_profile_at = refresh.retry_at
        remaining = max(0, refresh.retry_at - now)
        self.update_interval = timedelta(seconds=remaining)
        return ScheduledUpdateFailed(self.last_error, retry_after=remaining)

    async def _refresh_optional(self, kind):
        if not self._private_stats_enabled or kind in self._rejected_private:
            return
        path = POINTS if kind == "points" else BOOSTS
        now = time.time()
        self._due[kind] = now + EXTRA_SECONDS
        try:
            payload = await self.api.read_stats(path)
            clean = self._clean_values(kind, payload)
            if not clean:
                raise ApiError("Optional MakerWorld statistics have no recognized counters")
        except AuthError:
            self.extra_error[kind] = "Account token rejected; endpoint disabled until reauthentication"
            self._rejected_private[kind] = self._token_fingerprint
            self._due[kind] = 0
            self.connection_status = "partial"
            self.last_error = self.extra_error[kind]
        except (CloudflareError, RateLimitError, AccessDeniedError) as error:
            self.extra_error[kind] = str(error)
            self.last_error = str(error)
            await self._async_pause(error, kind)  # Record and persist; keep fresh profile.
        except ApiError as error:
            self.extra_error[kind] = str(error)
            self.connection_status = "partial"
            self.last_error = str(error)
        else:
            self._extras[kind] = clean
            self._extra_updated[kind] = time.time()
            self.extra_error[kind] = ""
            if self.pause["state"].strikes and self.pause["endpoint"] == kind:
                self.pause["state"].reset()
                await self._save_pause()
        await self._save_extras()
        if self.connection_status == "paused":
            self.update_interval = timedelta(seconds=max(0, self.pause["state"].until - time.time()))

    @callback
    def _async_refresh_finished(self):
        # HA skips its normal listener notification after consecutive failures.
        failed = not self.last_update_success
        if failed and self._previous_refresh_failed:
            self.async_update_listeners()
        self._previous_refresh_failed = failed

    async def _save_pause(self):
        payload = {
            **self.pause["state"].as_dict(),
            "endpoint": self.pause["endpoint"],
            "profile_retry_at": self.refresh.retry_at,
        }
        try:
            await self.pause_store.async_save(payload)
            # Store can log a write error without raising it to the caller.
            self.pause["persisted"] = await self.pause_store.async_load() == payload
        except STORAGE_ERRORS:
            self.pause["persisted"] = False
        if not self.pause["persisted"]:
            LOGGER.warning("Could not verify the persisted MakerWorld protection pause")

    def _pause_failure(self, remaining, detail=""):
        self.update_interval = timedelta(seconds=remaining)
        until = datetime.fromtimestamp(self.pause["state"].until, timezone.utc)
        kinds = {
            "cloudflare": "Cloudflare",
            "throttled": "Rate limit",
            "denied": "Access denied",
        }
        label = kinds.get(self.pause["state"].reason, "Protection pause")
        message = f"{label}: Requests paused until {until:%Y-%m-%d %H:%M} UTC."
        if not self.pause["persisted"]:
            message += " Could not save the protection pause."
        if detail:
            message += f" {detail}"
        return ScheduledUpdateFailed(message, retry_after=remaining)

    async def _async_pause(self, error, endpoint):
        state = self.pause["state"]
        if isinstance(error, CloudflareError):
            reason = "cloudflare"
        elif isinstance(error, RateLimitError):
            reason = "throttled"
        else:
            reason = "denied"
        state.deny(reason, time.time(), error.retry_after, random.uniform(0, 60))
        self.pause["endpoint"] = endpoint
        await self._save_pause()
        self.connection_status = "paused"
        self.next_profile_at = state.until
        return self._pause_failure(state.remaining(time.time()), str(error))
