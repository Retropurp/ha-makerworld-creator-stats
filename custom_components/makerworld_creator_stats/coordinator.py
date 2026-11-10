"""Refresh account statistics with persistent protection pauses."""

from datetime import datetime, timedelta, timezone
import logging
import time
import asyncio
import random

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .api import ApiError, AuthError
from .errors import CloudflareError, RateLimitError
from .backoff import Backoff
from .const import BOOSTS, DOMAIN, POINTS
from .profile import MakerWorldProfile
from .transactions import HISTORY_INTERVAL, TransactionError, read_cache


class MakerWorldCoordinator(DataUpdateCoordinator[MakerWorldProfile]):
    def __init__(self, hass, entry, api):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=30, seconds=random.uniform(0, 60)),
        )
        self.api = api
        self.account_id = entry.unique_id
        self.income_events = None
        self.history_synced_at = 0
        self.history_error = None
        self.history_attempted_at = 0
        self.history_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.transactions")
        self.history_persisted = True
        shared = hass.data.setdefault(DOMAIN, {}).setdefault("pauses", {})
        self.pause = shared.setdefault(entry.entry_id, {"state": Backoff(), "loaded": False, "persisted": True})
        self.pause_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.pause")

    async def _async_setup(self):
        if not self.pause["loaded"]:
            try:
                self.pause["state"].restore(await self.pause_store.async_load(), time.time())
            except (OSError, ValueError, TypeError, OverflowError):
                raise UpdateFailed(
                    "Gespeicherte Abfragepause nicht lesbar. Zum Schutz vor erneuten Anfragen wird gewartet.",
                    retry_after=3600,
                ) from None
            self.pause["loaded"] = True
        try:
            cached = read_cache(await self.history_store.async_load(), time.time())
        except (OSError, ValueError, TypeError, OverflowError):
            cached = None
        if cached is not None:
            self.history_synced_at, self.income_events = cached
            self.history_attempted_at = self.history_synced_at

    async def _async_update_data(self):
        remaining = self.pause["state"].remaining(time.time())
        if remaining:
            raise self._pause_failure(remaining)
        try:
            profile = await self.api.profile()
            if str(profile["uid"]) != self.account_id:
                raise ConfigEntryAuthFailed("Account changed. Sign in again")
            points = await self.api.optional_stats(POINTS)
            boosts = await self.api.optional_stats(BOOSTS)
            result = MakerWorldProfile.from_json(profile, points, boosts)
        except AuthError:
            raise ConfigEntryAuthFailed("Please sign in with a new email code") from None
        except (CloudflareError, RateLimitError) as error:
            raise await self._async_pause(error) from None
        except ApiError as error:
            self.update_interval = timedelta(hours=2)
            raise UpdateFailed(str(error)) from None
        except (AttributeError, TypeError, ValueError):
            self.update_interval = timedelta(hours=2)
            raise UpdateFailed("Unexpected statistics format") from None
        self.update_interval = timedelta(minutes=30, seconds=random.uniform(0, 60))
        now = time.time()
        if now - self.history_attempted_at >= HISTORY_INTERVAL:
            self.history_attempted_at = now
            try:
                async with asyncio.timeout(120):
                    events = await self.api.income_history(now)
            except AuthError:
                raise ConfigEntryAuthFailed("Please sign in again") from None
            except (CloudflareError, RateLimitError) as error:
                self.history_error = str(error)
                self.history_attempted_at = 0
                raise await self._async_pause(error) from None
            except TimeoutError:
                self.history_error = "History import timed out"
            except (ApiError, TransactionError) as error:
                self.history_error = str(error)
            else:
                self.income_events = events
                self.history_synced_at = now
                self.history_error = None
                try:
                    await self.history_store.async_save({"synced_at": now, "events": events})
                    self.history_persisted = True
                except OSError:
                    self.history_persisted = False
        if self.pause["state"].strikes:
            self.pause["state"].reset()
            await self._async_save_pause()
        return result

    async def _async_save_pause(self):
        try:
            await self.pause_store.async_save(self.pause["state"].as_dict())
            self.pause["persisted"] = True
        except OSError:
            self.pause["persisted"] = False

    def _pause_failure(self, remaining, detail=""):
        until = datetime.fromtimestamp(self.pause["state"].until, timezone.utc)
        reason = "Cloudflare" if self.pause["state"].reason == "cloudflare" else "Anfragebegrenzung"
        message = f"{reason}: Abfragepause bis {until:%d.%m.%Y %H:%M} UTC. Bis dahin keine Statistikabfragen."
        if not self.pause["persisted"]:
            message += " Pause konnte nicht dauerhaft gespeichert werden; Home Assistant vorerst nicht neu starten."
        if detail:
            message += f" {detail}"
        return UpdateFailed(message, retry_after=remaining)

    async def _async_pause(self, error):
        state = self.pause["state"]
        state.deny(
            "cloudflare" if isinstance(error, CloudflareError) else "throttled",
            time.time(), error.retry_after, random.uniform(0, 60),
        )
        await self._async_save_pause()
        return self._pause_failure(state.remaining(time.time()), str(error))
