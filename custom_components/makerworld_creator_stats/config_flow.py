"""Password-free setup and reauthentication through an email code."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiError, AuthError, CodeError, MakerWorldApi
from .const import DOMAIN


class MakerWorldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._email = ""
        self._api = None

    async def async_step_user(self, user_input=None):
        errors = {}
        detail = ""
        if user_input is not None:
            email = user_input["email"].strip()
            if "@" not in email or len(email) > 254:
                errors["email"] = "invalid_email"
            else:
                self._email = email
                self._api = MakerWorldApi(async_get_clientsession(self.hass))
                try:
                    await self._api.request_code(email)
                except ApiError as error:
                    detail = str(error)
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_code()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("email", default=self._email): str}),
            errors=errors,
            description_placeholders={"detail": detail},
        )

    async def async_step_code(self, user_input=None):
        errors = {}
        detail = ""
        if user_input is not None:
            if user_input.get("resend", False):
                try:
                    await self._api.request_code(self._email)
                except ApiError as error:
                    detail = str(error)
                    errors["base"] = "cannot_connect"
            else:
                try:
                    token = await self._api.login(self._email, user_input["code"].strip())
                    profile = await self._api.profile()
                except (CodeError, AuthError):
                    errors["base"] = "invalid_code"
                except ApiError as error:
                    detail = str(error)
                    errors["base"] = "cannot_connect"
                else:
                    uid = str(profile["uid"])
                    if self.source == config_entries.SOURCE_REAUTH:
                        entry = self._get_reauth_entry()
                        if uid != entry.unique_id:
                            return self.async_abort(reason="wrong_account")
                        return self.async_update_reload_and_abort(
                            entry, data_updates={"email": self._email, "token": token}
                        )
                    await self.async_set_unique_id(uid)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"MakerWorld {profile.get('name') or uid}",
                        data={"email": self._email, "token": token},
                    )
        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema({
                vol.Required("code", default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Optional("resend", default=False): bool,
            }),
            errors=errors,
            description_placeholders={"detail": detail},
        )

    async def async_step_reauth(self, entry_data):
        self._email = entry_data["email"]
        return await self.async_step_user()
