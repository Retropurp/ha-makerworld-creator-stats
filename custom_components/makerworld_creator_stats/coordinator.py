"""Refresh MakerWorld statistics every fifteen minutes."""

from datetime import timedelta
import logging
import time
import asyncio

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .api import ApiError, AuthError
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
            update_interval=timedelta(minutes=15),
        )
        self.api = api
        self.account_id = entry.unique_id
        self.income_events = None
        self.history_synced_at = 0
        self.history_error = None
        self.history_attempted_at = 0
        self.history_store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.transactions")
        self.history_persisted = True

    async def _async_setup(self):
        try:
            cached = read_cache(await self.history_store.async_load(), time.time())
        except (OSError, ValueError, TypeError, OverflowError):
            cached = None
        if cached is not None:
            self.history_synced_at, self.income_events = cached
            self.history_attempted_at = self.history_synced_at

    async def _async_update_data(self):
        try:
            profile = await self.api.profile()
            if str(profile["uid"]) != self.account_id:
                raise ConfigEntryAuthFailed("Account changed. Sign in again")
            points = await self.api.optional_stats(POINTS)
            boosts = await self.api.optional_stats(BOOSTS)
            result = MakerWorldProfile.from_json(profile, points, boosts)
        except AuthError:
            raise ConfigEntryAuthFailed("Please sign in with a new email code") from None
        except ApiError as error:
            self.update_interval = timedelta(hours=2)
            raise UpdateFailed(str(error)) from None
        except (AttributeError, TypeError, ValueError):
            self.update_interval = timedelta(hours=2)
            raise UpdateFailed("Unexpected statistics format") from None
        self.update_interval = timedelta(minutes=15)
        now = time.time()
        if now - self.history_attempted_at >= HISTORY_INTERVAL:
            self.history_attempted_at = now
            try:
                async with asyncio.timeout(120):
                    events = await self.api.income_history(now)
            except AuthError:
                raise ConfigEntryAuthFailed("Please sign in again") from None
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
        return result
