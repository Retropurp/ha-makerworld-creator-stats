"""Exercise the real coordinator with simulated HA storage and scheduling."""

import asyncio
import copy
from datetime import datetime, timezone
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, call, patch
from test_rewards import COMPONENT

package = types.ModuleType("pause_test_package")
package.__path__ = [str(COMPONENT)]
sys.modules[package.__name__] = package
errors = importlib.import_module("pause_test_package.errors")


class HomeAssistantError(Exception):
    pass


class UpdateFailed(HomeAssistantError):
    pass


class ConfigEntryAuthFailed(HomeAssistantError):
    pass


class Coordinator:
    def __class_getitem__(cls, arg):
        return cls

    def __init__(self, hass, logger, **kwargs):
        self.hass = hass
        self.update_interval = kwargs["update_interval"]
        self.last_update_success = True
        self.data = None
        self.listeners = []

    def async_update_listeners(self):
        for listener in self.listeners:
            listener()

    async def async_request_refresh(self):
        await self.async_refresh()

    async def async_refresh(self):
        previous_success = self.last_update_success
        try:
            self.data = await self._async_update_data()
        except (UpdateFailed, ConfigEntryAuthFailed):
            self.last_update_success = False
        else:
            self.last_update_success = True
        self._async_refresh_finished()
        if self.last_update_success or previous_success:
            self.async_update_listeners()


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def available(self):
        return self.coordinator.last_update_success


class Store:
    data = {}
    unreadable = False
    unwritable = False

    def __init__(self, hass, version, key):
        self.key = key

    async def async_load(self):
        if self.unreadable:
            raise OSError("unreadable")
        return copy.deepcopy(self.data.get(self.key))

    async def async_save(self, value):
        if self.unwritable:
            raise OSError("unwritable")
        self.data[self.key] = copy.deepcopy(value)


modules = {name: types.ModuleType(name) for name in (
    "homeassistant", "homeassistant.core", "homeassistant.exceptions", "homeassistant.helpers",
    "homeassistant.helpers.update_coordinator", "homeassistant.helpers.storage",
    "homeassistant.helpers.entity", "homeassistant.helpers.entity_registry",
    "homeassistant.helpers.translation",
    "homeassistant.components", "homeassistant.components.sensor", "aiohttp",
)}
modules["homeassistant.core"].callback = lambda fn: fn
modules["homeassistant.exceptions"].ConfigEntryAuthFailed = ConfigEntryAuthFailed
modules["homeassistant.exceptions"].HomeAssistantError = HomeAssistantError
modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = Coordinator
modules["homeassistant.helpers.update_coordinator"].UpdateFailed = UpdateFailed
modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity
modules["homeassistant.helpers.storage"].Store = Store
modules["homeassistant.helpers.entity"].EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
modules["homeassistant.helpers.entity"].DeviceInfo = dict
registry = modules["homeassistant.helpers.entity_registry"]
registry.async_get = lambda hass: None
registry.async_entries_for_config_entry = lambda registry, entry_id: ()
modules["homeassistant.helpers.translation"].async_get_translations = AsyncMock(return_value={})
sensor_module = modules["homeassistant.components.sensor"]
sensor_module.SensorEntity = object
sensor_module.SensorEntityDescription = types.SimpleNamespace
sensor_module.SensorDeviceClass = types.SimpleNamespace(TIMESTAMP="timestamp", ENUM="enum")
sensor_module.SensorStateClass = types.SimpleNamespace(MEASUREMENT="measurement")
modules["aiohttp"].ClientError = type("ClientError", (Exception,), {})
modules["aiohttp"].ClientSession = object
modules["aiohttp"].ClientTimeout = types.SimpleNamespace
with patch.dict(sys.modules, modules):
    coordinator = importlib.import_module("pause_test_package.coordinator")
    sensor = importlib.import_module("pause_test_package.sensor")
    api = importlib.import_module("pause_test_package.api")


class PauseCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Store.data, Store.unreadable, Store.unwritable = {}, False, False
        self.now = 1000000
        self.clock = patch.object(coordinator.time, "time", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.jitter_patch = patch.object(coordinator.random, "uniform", return_value=0)
        self.jitter = self.jitter_patch.start()
        self.addCleanup(self.jitter_patch.stop)
        self.hass = types.SimpleNamespace(data={}, config=types.SimpleNamespace(language="en"))
        self.entry = types.SimpleNamespace(entry_id="entry", unique_id="42", options={}, data={})
        self.api = types.SimpleNamespace(
            token="test-token",
            profile=AsyncMock(return_value={"uid": 42, "name": "Test"}),
            read_stats=AsyncMock(return_value={"totalRegularIncome": 12, "availableTotal": 3}),
            income_history=AsyncMock(return_value=[]),
        )
        self.addCleanup(self.api.income_history.assert_not_awaited)

    async def create(self, hass=None):
        result = coordinator.MakerWorldCoordinator(hass or self.hass, self.entry, self.api)
        await result._async_setup()
        return result

    async def deny(self, result):
        self.api.profile.side_effect = errors.CloudflareError("Cloudflare")
        with self.assertRaises(UpdateFailed):
            await result._async_update_data()
        self.api.profile.side_effect = None
        self.api.profile.reset_mock()

    async def test_pause_blocks_requests_and_survives_reload(self):
        first = await self.create()
        await self.deny(first)
        for instance in (first, await self.create()):
            with self.assertRaises(UpdateFailed) as caught:
                await instance._async_update_data()
            self.assertEqual(caught.exception.retry_after, 7200)
        self.api.profile.assert_not_awaited()
        self.api.read_stats.assert_not_awaited()

    async def test_restart_reads_persisted_pause(self):
        await self.deny(await self.create())
        self.now += 600
        restarted = await self.create(types.SimpleNamespace(data={}))
        with self.assertRaises(UpdateFailed) as caught:
            await restarted._async_update_data()
        self.assertEqual(caught.exception.retry_after, 6600)
        self.api.profile.assert_not_awaited()

    async def test_repeated_block_escalates_after_restart(self):
        await self.deny(await self.create())
        self.now += 7201
        restarted = await self.create(types.SimpleNamespace(data={}))
        await self.deny(restarted)
        self.assertEqual(restarted.pause["state"].remaining(self.now), 14400)

    async def test_recovery_resumes_normal_interval_and_resets_counter(self):
        result = await self.create()
        await self.deny(result)
        self.now += 7201
        await result._async_update_data()
        self.assertEqual(result.pause["state"].strikes, 0)
        self.assertEqual(result.update_interval.total_seconds(), 3600)
        self.assertEqual(Store.data[result.pause_store.key]["until"], 0)

    async def test_ordinary_startup_failure_waits_across_reload_and_restart(self):
        first = await self.create()
        self.api.profile.side_effect = errors.ApiError("Network error")
        with self.assertRaises(coordinator.ScheduledUpdateFailed) as caught:
            await first._async_update_data()
        self.assertEqual(caught.exception.retry_after, 7200)
        self.assertEqual(Store.data[first.pause_store.key]["profile_retry_at"], self.now + 7200)
        self.api.profile.side_effect = None
        self.now += 5
        reloaded = await self.create()
        restarted = await self.create(types.SimpleNamespace(data={}))
        for instance in (first, reloaded, restarted):
            with self.assertRaises(coordinator.ScheduledUpdateFailed) as pending:
                await instance._async_update_data()
            self.assertEqual(pending.exception.retry_after, 7195)
        self.api.profile.assert_awaited_once()
        self.api.read_stats.assert_not_awaited()
        self.now += 7195
        await restarted.async_refresh()
        self.assertEqual(self.api.profile.await_count, 2)
        self.api.read_stats.assert_not_awaited()
        self.assertEqual(restarted.connection_status, "success")

    async def test_reloads_use_existing_profile_and_keep_optional_schedule(self):
        first = await self.create()
        await first.async_refresh()
        self.now += 60
        reloaded = await self.create()
        await reloaded.async_refresh()
        await reloaded.async_request_refresh()
        self.assertEqual(reloaded.data.name, "Test")
        self.assertEqual(reloaded.last_profile_success, self.now - 60)
        self.assertEqual(reloaded.next_profile_update, self.now + 3540)
        self.assertEqual(reloaded.update_interval.total_seconds(), 3540)
        self.api.profile.assert_awaited_once()
        self.api.read_stats.assert_not_awaited()
        self.now += 3540
        await reloaded.async_refresh()
        self.assertEqual(self.api.profile.await_count, 2)
        self.api.read_stats.assert_awaited_once_with(coordinator.POINTS)

    async def test_concurrent_refreshes_at_due_time_share_one_profile_request(self):
        first = await self.create()
        second = await self.create()
        request_started = asyncio.Event()
        release_request = asyncio.Event()

        async def profile():
            request_started.set()
            await release_request.wait()
            return {"uid": 42}

        self.api.profile.side_effect = profile
        async with asyncio.TaskGroup() as group:
            group.create_task(first.async_refresh())
            await request_started.wait()
            group.create_task(second.async_refresh())
            release_request.set()
        self.api.profile.assert_awaited_once()
        self.api.read_stats.assert_not_awaited()
        self.assertEqual(first.data, second.data)

    async def test_failed_persistence_still_blocks_in_process_retry(self):
        first = await self.create()
        Store.unwritable = True
        self.api.profile.side_effect = errors.ApiError("Network error")
        with self.assertRaises(coordinator.ScheduledUpdateFailed):
            await first._async_update_data()
        self.assertFalse(first.pause["persisted"])
        with self.assertRaises(coordinator.ScheduledUpdateFailed):
            await (await self.create())._async_update_data()
        self.api.profile.assert_awaited_once()

    async def test_optional_throttle_keeps_profile_and_pauses_every_endpoint(self):
        result = await self.create()
        await result._async_update_data()
        self.now += 3600
        self.api.read_stats.side_effect = errors.RateLimitError("Rate limited", retry_after=10000)
        profile = await result._async_update_data()
        self.assertEqual(profile.name, "Test")
        self.assertEqual(result.connection_status, "paused")
        self.assertEqual(result.next_profile_update, self.now + 10000)
        self.assertEqual(result.update_interval.total_seconds(), 10000)
        self.api.profile.reset_mock()
        with self.assertRaises(UpdateFailed):
            await result._async_update_data()
        self.api.read_stats.assert_awaited_once_with(coordinator.POINTS)
        self.api.profile.assert_not_awaited()

    async def test_profile_cadence_and_independent_optional_intervals(self):
        result = await self.create()
        self.jitter.side_effect = [60, 0, 60, 0, 60, 0, 60]
        for cycle in range(7):
            optional_before = self.api.read_stats.await_count
            await result.async_refresh()
            self.assertEqual(self.api.profile.await_count, cycle + 1)
            self.assertLessEqual(self.api.read_stats.await_count - optional_before, 1)
            step = result.update_interval.total_seconds()
            self.assertIn(step, (3600, 3660))
            self.assertEqual(result.next_profile_update, self.now + step)
            await result.async_request_refresh()
            self.assertEqual(self.api.profile.await_count, cycle + 1)
            self.now += step
        self.assertEqual(self.api.read_stats.await_args_list, [
            call(coordinator.POINTS), call(coordinator.BOOSTS),
        ])
        self.assertGreaterEqual(result._due["points"], 1000000 + 3600 + 21600)
        self.assertGreaterEqual(result._due["boosts"], 1000000 + 7200 + 21600)

    async def test_overdue_cache_is_reused_on_restart_and_expires_after_failure(self):
        result = await self.create()
        await result._async_update_data()
        self.now += 3600
        self.assertEqual((await result._async_update_data()).points_earned, 12)
        self.now += 7201
        restarted = await self.create(types.SimpleNamespace(data={}))
        self.api.read_stats.reset_mock()
        self.assertEqual((await restarted._async_update_data()).points_earned, 12)
        self.api.read_stats.assert_not_awaited()
        self.now += 14400
        self.api.read_stats.side_effect = errors.ApiError("Offline")
        self.assertEqual((await restarted._async_update_data()).points_earned, 12)
        self.assertEqual(restarted.connection_status, "partial")
        due = restarted._due["points"]
        self.now += 7201
        again = await self.create(types.SimpleNamespace(data={}))
        self.assertEqual(again._due["points"], due)
        self.assertIsNone((await again._async_update_data()).points_earned)
        self.api.read_stats.assert_awaited_once_with(coordinator.POINTS)

    async def test_optional_denial_escalates_after_profile_only_restart(self):
        result = await self.create()
        await result._async_update_data()
        self.now += 3600
        self.api.read_stats.side_effect = errors.AccessDeniedError("HTTP 403")
        await result._async_update_data()
        self.now += 7201
        restarted = await self.create(types.SimpleNamespace(data={}))
        await restarted._async_update_data()
        self.assertEqual(restarted.pause["state"].strikes, 1)
        self.now = restarted._due["points"]
        await restarted._async_update_data()
        self.assertEqual(restarted.pause["state"].remaining(self.now), 14400)

    async def test_private_stats_opt_out_never_calls_restricted_endpoints(self):
        self.entry.data["private_stats_enabled"] = False
        result = await self.create()
        for _ in range(9):
            await result._async_update_data()
            self.now += 3600
        self.api.read_stats.assert_not_awaited()
        self.assertIsNone(result.next_points_at)
        self.assertIsNone(result.next_boosts_at)
        self.assertEqual(result.connection_status, "success")

    async def test_private_401_stops_until_new_token_even_after_restart(self):
        result = await self.create()
        await result._async_update_data()
        self.now += 3600
        self.api.read_stats.side_effect = errors.AuthError("Token rejected")
        await result._async_update_data()
        self.api.read_stats.assert_awaited_once_with(coordinator.POINTS)
        self.assertIsNone(result.next_points_at)
        self.now += 21600
        restarted = await self.create(types.SimpleNamespace(data={}))
        self.api.read_stats.reset_mock()
        await restarted._async_update_data()
        self.api.read_stats.assert_not_awaited()
        self.assertIsNone(restarted.next_points_at)
        self.api.token = "new-token"
        self.api.read_stats.side_effect = None
        reauthed = await self.create(types.SimpleNamespace(data={}))
        self.assertIsNotNone(reauthed.next_points_at)
        await reauthed._async_update_data()
        self.now += 3600
        await reauthed._async_update_data()
        self.api.read_stats.assert_awaited_once_with(coordinator.POINTS)

    async def test_diagnostics_update_while_profile_is_unavailable(self):
        result = await self.create()
        await result.async_refresh()
        self.entry.runtime_data = result
        entities = []
        await sensor.async_setup_entry(self.hass, self.entry, entities.extend)
        by_id = {entity._attr_unique_id: entity for entity in entities}
        self.assertEqual(len(entities), len(by_id))
        self.assertIn("42_design_downloads", by_id)
        self.assertIn("42_points", by_id)
        self.assertIn("42_boost_tokens", by_id)
        expected = {
            key for key, *_ in (*sensor.SENSORS, *sensor.DIAGNOSTIC_SENSORS,
                                *sensor.REWARD_SENSORS, *sensor.CASH_SENSORS)
        }
        expected.update(
            f"income_{kind}_{days}d" for kind in ("points", "money", "cash") for days in (7, 14, 30)
        )
        self.assertEqual(set(by_id), {f"42_{key}" for key in expected})
        for key in expected:
            entity = by_id[f"42_{key}"]
            self.assertEqual(entity.entity_description.translation_key, key)
            if key.startswith("income_"):
                self.assertIsNone(entity.native_value)
                self.assertFalse(entity.available)
        status = by_id["42_connection_status"]
        timestamp = by_id["42_next_profile_update"]
        last_success = by_id["42_last_profile_success"]
        self.assertEqual(timestamp.entity_description.device_class, "timestamp")
        self.assertEqual(status._attr_entity_category, "diagnostic")
        self.assertEqual(status.entity_description.device_class, "enum")
        self.assertEqual(tuple(status.entity_description.options), sensor.CONNECTION_STATES)
        self.assertEqual(set(status.extra_state_attributes), {"detail", "punkte_fehler", "boost_fehler"})
        observed = []
        result.listeners.append(lambda: observed.append((status.native_value, timestamp.native_value)))
        self.now += 3600
        self.api.profile.side_effect = errors.ApiError("Offline")
        await result.async_refresh()
        self.now += 7200
        self.api.profile.side_effect = errors.AccessDeniedError("403")
        await result.async_refresh()
        self.assertEqual([state for state, _ in observed], ["error", "paused"])
        self.assertEqual(observed[-1][1], datetime.fromtimestamp(self.now + 7200, timezone.utc))
        self.assertEqual(last_success.native_value, datetime.fromtimestamp(1000000, timezone.utc))
        self.assertTrue(status.available)
        self.assertFalse(by_id["42_design_downloads"].available)
        self.assertEqual(status.extra_state_attributes["detail"], "403")
        self.api.read_stats.assert_not_awaited()

    async def test_malformed_profile_does_not_trigger_optional_request(self):
        result = await self.create()
        await result._async_update_data()
        self.now += 3600
        self.api.profile.return_value = {"uid": 42, "MWCount": "invalid"}
        with self.assertRaises(UpdateFailed):
            await result._async_update_data()
        self.assertEqual(result.last_profile_success, 1000000)
        self.assertEqual(result.connection_status, "error")
        self.api.read_stats.assert_not_awaited()

    async def test_unreadable_pause_does_not_trigger_network(self):
        Store.unreadable = True
        with self.assertRaises(UpdateFailed):
            await self.create()
        self.api.profile.assert_not_awaited()

    async def test_save_failure_keeps_pause_in_memory(self):
        result = await self.create()
        Store.unwritable = True
        await self.deny(result)
        with self.assertRaises(UpdateFailed) as caught:
            await result._async_update_data()
        self.assertIn("Could not save the protection pause", str(caught.exception))
        self.api.profile.assert_not_awaited()

    async def test_store_that_swallows_write_error_still_keeps_pause(self):
        result = await self.create()
        with patch.object(result.pause_store, "async_save", new=AsyncMock()):
            await self.deny(result)
        self.assertFalse(result.pause["persisted"])
        self.assertEqual(result.pause["state"].remaining(self.now), 7200)

    async def test_rejected_account_stops_updates_until_reauthentication(self):
        result = await self.create()
        await result.async_refresh()
        self.now += 3600
        self.api.profile.return_value = {"uid": 99, "name": "Other account"}
        await result.async_refresh()
        self.assertEqual(result.connection_status, "auth_required")
        self.assertIsNone(result.next_profile_update)
        self.assertIsNone(result.next_points_at)
        self.assertIsNone(result.next_boosts_at)
        await result.async_request_refresh()
        self.assertEqual(self.api.profile.await_count, 2)
        self.api.read_stats.assert_not_awaited()


class ApiRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_denials_and_challenge_header_are_classified_without_retry(self):
        for status, headers, expected in (
            (403, {"Retry-After": "9000"}, errors.AccessDeniedError),
            (429, {"Retry-After": "9000"}, errors.RateLimitError),
            (503, {"CF-Mitigated": "challenge", "Retry-After": "9000"}, errors.CloudflareError),
        ):
            with self.subTest(status=status):
                context = AsyncMock()
                context.__aenter__.return_value = types.SimpleNamespace(
                    status=status, headers=headers,
                    content=types.SimpleNamespace(read=AsyncMock(side_effect=TimeoutError)),
                )
                session = types.SimpleNamespace(request=Mock(return_value=context))
                client = api.MakerWorldApi(session, "offline-token")
                with self.assertRaises(expected) as caught:
                    await client.read_stats(coordinator.POINTS)
                self.assertEqual(caught.exception.retry_after, 9000)
                self.assertEqual(session.request.call_count, 1)
                self.assertFalse(session.request.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
