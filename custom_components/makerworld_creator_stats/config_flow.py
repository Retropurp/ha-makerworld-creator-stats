"""Password-free setup and reauthentication through an email code."""

from decimal import Decimal

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiError, AuthError, CodeError, MakerWorldApi
from .const import DOMAIN
from .rewards import BASES, PRESETS, REGIONS, number


class MakerWorldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RewardsOptionsFlow(config_entry)

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


class RewardsOptionsFlow(config_entries.OptionsFlow):
    """Choose a shop first, then confirm editable gift-card terms."""

    def __init__(self, entry):
        self._settings = dict(entry.options)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            region = user_input["shop_region"]
            changed = region != self._settings.get("shop_region")
            self._settings.update(user_input)
            if region in ("unset", "cn"):
                return self.async_create_entry(title="", data=self._settings)
            if changed:
                currency, value, points = PRESETS.get(region, ("EUR", 40, 524))
                self._settings.update(currency=currency, card_value=value, card_points=points)
            return await self.async_step_terms()
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("shop_region", default=self._settings.get("shop_region", "unset")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": key, "label": label} for key, label in REGIONS.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("points_basis", default=self._settings.get("points_basis", "regular")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": key, "label": label} for key, label in BASES.items()],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }),
        )

    async def async_step_terms(self, user_input=None):
        errors = {}
        if user_input is not None:
            currency = user_input["currency"].strip().upper()
            value = number(user_input["card_value"])
            points = number(user_input["card_points"])
            if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
                errors["currency"] = "invalid_currency"
            if value is None or not Decimal("0.000001") <= value <= 10**12:
                errors["card_value"] = "invalid_amount"
            if points is None or not Decimal("0.000001") <= points <= 10**12:
                errors["card_points"] = "invalid_amount"
            if not errors:
                self._settings.update(currency=currency, card_value=str(value), card_points=str(points))
                return self.async_create_entry(title="", data=self._settings)
        return self.async_show_form(
            step_id="terms",
            data_schema=vol.Schema({
                vol.Required("currency", default=self._settings.get("currency", "EUR")): str,
                vol.Required("card_value", default=str(self._settings.get("card_value", 40))): str,
                vol.Required("card_points", default=str(self._settings.get("card_points", 524))): str,
            }),
            errors=errors,
        )
