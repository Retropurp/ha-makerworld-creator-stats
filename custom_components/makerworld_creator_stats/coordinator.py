"""Coordinated, rate-conscious MakerWorld account polling."""

from datetime import datetime, timedelta, timezone
import logging
import random
import time

from homeassistant.exceptions import ConfigEntryAuthFailed
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


class MakerWorldCoordinator(DataUpdateCoordinator[MakerWorldProfile]):
    """One creator profile every 30m, up to one optional GET per refresh."""

    def __init__(self, hass, entry, api):
        super().__init__(
            hass, LOGGER, name=DOMAIN, config_entry=entry,
            update_interval=self._profile_interval(),
        )
        self.api = api
        self.account_id = entry.unique_id
        self.income_events = None
        self.history_synced_at = 0
        self.history_error = "Historical transaction import disabled in beta 2"
        self.history_persisted = True
        self.reward_options = dict(entry.options)

        shared = hass.data.setdefault(DOMAIN, {}).setdefault("pauses", {})
        self.pause = shared.setdefault(
            entry.entry_id, {"state": Backoff(), "loaded": False, "persisted": True},
        )
        self.pause_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.pause")

        self.extras_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.extras")
        self._extras = {kind: {} for kind in EXTRA_KEYS}
        self._extra_updated = {kind: 0.0 for kind in EXTRA_KEYS}
        self._due = {kind: 0.0 for kind in EXTRA_KEYS}
        self.extra_error = {kind: "" for kind in EXTRA_KEYS}

        self.last_profile_success = 0.0
        self.next_profile_at = 0.0
        self.last_error = ""
        self.connection_status = "initializing"

    @staticmethod
    def _profile_interval():
        return timedelta(seconds=PROFILE_SECONDS + random.uniform(0, 60))

    async def _async_setup(self):
        if not self.pause["loaded"]:
            try:
                self.pause["state"].restore(
                    await self.pause_store.async_load(), time.time(),
                )
            except (OSError, ValueError, TypeError, OverflowError):
                raise UpdateFailed(
                    "Gespeicherte Schutzpause nicht lesbar; keine Anfrage wird gestartet.",
                    retry_after=3600,
                ) from None
            self.pause["loaded"] = True

        now = time.time()
        self._due = first_due(now)
        try:
            cache = await self.extras_store.async_load()
        except (OSError, ValueError, TypeError, OverflowError):
            cache = None
        if isinstance(cache, dict) and cache.get("account_id") == self.account_id:
            for kind, fields in EXTRA_KEYS.items():
                stored = cache.get(kind)
                if not isinstance(stored, dict):
                    continue
                stamp = stored.get("updated_at")
                values = stored.get("values")
                if not valid_timestamp(stamp, now) or not isinstance(values, dict):
                    continue
                clean = self._clean_values(kind, values)
                if clean:
                    self._extras[kind] = clean
                    self._extra_updated[kind] = float(stamp)
                    self._due[kind] = max(float(stamp) + EXTRA_SECONDS, now)

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
        payload = {"account_id": self.account_id}
        for kind in EXTRA_KEYS:
            payload[kind] = {
                "updated_at": self._extra_updated[kind],
                "values": self._extras[kind],
            }
        try:
            await self.extras_store.async_save(payload)
        except OSError:
            LOGGER.warning("Could not persist MakerWorld optional-statistics cache")

    def _current_extra(self, kind, now):
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
        due = self._due[kind]
        if not due:
            return None
        remaining = self.pause["state"].remaining(time.time())
        return max(due, self.pause["state"].until) if remaining else due

    @property
    def next_profile_update(self):
        remaining = self.pause["state"].remaining(time.time())
        if remaining:
            return max(self.next_profile_at, self.pause["state"].until)
        return self.next_profile_at or None

    async def _async_update_data(self):
        now = time.time()
        remaining = self.pause["state"].remaining(now)
        if remaining:
            self.connection_status = "paused"
            self.next_profile_at = self.pause["state"].until
            raise self._pause_failure(remaining)

        try:
            raw_profile = await self.api.profile()
            if str(raw_profile["uid"]) != self.account_id:
                raise ConfigEntryAuthFailed("MakerWorld account changed; sign in again")
        except AuthError:
            self.connection_status = "auth_required"
            self.last_error = "Authentication required"
            raise ConfigEntryAuthFailed("Please sign in with a new email code") from None
        except (CloudflareError, RateLimitError, AccessDeniedError) as error:
            self.last_error = str(error)
            raise await self._async_pause(error) from None
        except ApiError as error:
            self.connection_status = "error"
            self.last_error = str(error)
            self.update_interval = timedelta(hours=2)
            self.next_profile_at = time.time() + 2 * 3600
            raise UpdateFailed(str(error)) from None
        except (AttributeError, TypeError, ValueError):
            self.connection_status = "error"
            self.last_error = "Unexpected profile format"
            self.update_interval = timedelta(hours=2)
            self.next_profile_at = time.time() + 2 * 3600
            raise UpdateFailed(self.last_error) from None

        now = time.time()
        self.last_profile_success = now
        self.update_interval = self._profile_interval()
        self.next_profile_at = now + self.update_interval.total_seconds()
        self.connection_status = "success"
        self.last_error = ""

        # First update is profile-only. Restore/cache optional data without
        # launching a burst of requests on every startup or account reload.
        chosen = due_optional(self._due, now)
        if chosen is not None:
            await self._refresh_optional(chosen)

        if not self.pause["state"].remaining(time.time()):
            if any(self.extra_error.values()):
                # A healthy profile does not imply optional endpoints succeeded.
                self.connection_status = "partial"
            if self.pause["state"].strikes:
                self.pause["state"].reset()
                await self._save_pause()

        now = time.time()
        return MakerWorldProfile.from_json(
            raw_profile, self._current_extra("points", now),
            self._current_extra("boosts", now),
        )

    async def _refresh_optional(self, kind):
        path = POINTS if kind == "points" else BOOSTS
        now = time.time()
        self._due[kind] = now + EXTRA_SECONDS
        try:
            payload = await self.api.read_stats(path)
            clean = self._clean_values(kind, payload)
            if not clean:
                raise ApiError("Optional MakerWorld statistics have no recognized counters")
        except AuthError:
            self.extra_error[kind] = "Account token rejected for optional statistics"
            self._due[kind] = now + 6 * 3600
            self.connection_status = "partial"
            self.last_error = self.extra_error[kind]
        except (CloudflareError, RateLimitError, AccessDeniedError) as error:
            self.extra_error[kind] = str(error)
            self.last_error = str(error)
            self._due[kind] = now + EXTRA_SECONDS
            await self._async_pause(error)  # Record and persist; keep fresh profile.
        except ApiError as error:
            self.extra_error[kind] = str(error)
            self.connection_status = "partial"
            self.last_error = str(error)
        else:
            self._extras[kind] = clean
            self._extra_updated[kind] = time.time()
            self.extra_error[kind] = ""
            await self._save_extras()

    async def _save_pause(self):
        try:
            await self.pause_store.async_save(self.pause["state"].as_dict())
            self.pause["persisted"] = True
        except OSError:
            self.pause["persisted"] = False

    def _pause_failure(self, remaining, detail=""):
        until = datetime.fromtimestamp(self.pause["state"].until, timezone.utc)
        kinds = {
            "cloudflare": "Cloudflare",
            "throttled": "Anfragebegrenzung",
            "denied": "Zugriff abgewiesen",
        }
        label = kinds.get(self.pause["state"].reason, "Anfragepause")
        message = f"{label}: Keine Anfragen bis {until:%d.%m.%Y %H:%M} UTC."
        if not self.pause["persisted"]:
            message += " Schutzpause konnte nicht gespeichert werden."
        if detail:
            message += f" {detail}"
        return UpdateFailed(message, retry_after=remaining)

    async def _async_pause(self, error):
        state = self.pause["state"]
        if isinstance(error, CloudflareError):
            reason = "cloudflare"
        elif isinstance(error, RateLimitError):
            reason = "throttled"
        else:
            reason = "denied"
        state.deny(reason, time.time(), error.retry_after, random.uniform(0, 60))
        await self._save_pause()
        self.connection_status = "paused"
        self.next_profile_at = state.until
        return self._pause_failure(state.remaining(time.time()), str(error))
