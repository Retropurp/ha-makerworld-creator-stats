"""Refresh MakerWorld statistics every fifteen minutes."""

from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, AuthError
from .const import BOOSTS, DOMAIN, POINTS
from .profile import MakerWorldProfile


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
        return result
