"""Exercise the real coordinator with simulated HA storage and scheduling."""

import copy
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch
from test_rewards import COMPONENT

package = types.ModuleType("pause_test_package")
package.__path__ = [str(COMPONENT)]
sys.modules[package.__name__] = package
errors = importlib.import_module("pause_test_package.errors")


class UpdateFailed(Exception):
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class Coordinator:
    def __class_getitem__(cls, arg):
        return cls

    def __init__(self, hass, logger, **kwargs):
        self.hass = hass
        self.update_interval = kwargs["update_interval"]


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
    "homeassistant", "homeassistant.exceptions", "homeassistant.helpers",
    "homeassistant.helpers.update_coordinator", "homeassistant.helpers.storage",
    "pause_test_package.api",
)}
modules["homeassistant.exceptions"].ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})
modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = Coordinator
modules["homeassistant.helpers.update_coordinator"].UpdateFailed = UpdateFailed
modules["homeassistant.helpers.storage"].Store = Store
modules["pause_test_package.api"].ApiError = errors.ApiError
modules["pause_test_package.api"].AuthError = errors.AuthError
with patch.dict(sys.modules, modules):
    coordinator = importlib.import_module("pause_test_package.coordinator")


class PauseCoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        Store.data, Store.unreadable, Store.unwritable = {}, False, False
        self.now = 1000000
        self.clock = patch.object(coordinator.time, "time", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.jitter = patch.object(coordinator.random, "uniform", return_value=0)
        self.jitter.start()
        self.addCleanup(self.jitter.stop)
        self.hass = types.SimpleNamespace(data={})
        self.entry = types.SimpleNamespace(entry_id="entry", unique_id="42")
        self.api = types.SimpleNamespace(
            profile=AsyncMock(return_value={"uid": 42, "name": "Test"}),
            optional_stats=AsyncMock(return_value={}), income_history=AsyncMock(return_value=[]),
        )

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
        self.api.optional_stats.assert_not_awaited()
        self.api.income_history.assert_not_awaited()

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
        self.assertEqual(result.update_interval.total_seconds(), 1800)
        self.assertEqual(Store.data[result.pause_store.key]["until"], 0)

    async def test_history_block_stops_update_and_retries_history_after_pause(self):
        result = await self.create()
        self.api.income_history.side_effect = errors.CloudflareError("Cloudflare")
        with self.assertRaises(UpdateFailed):
            await result._async_update_data()
        self.assertEqual(result.history_attempted_at, 0)
        self.api.income_history.side_effect = None
        self.now += 7201
        await result._async_update_data()
        self.assertEqual(self.api.income_history.await_count, 2)
        self.assertEqual(result.pause["state"].strikes, 0)

    async def test_optional_throttle_stops_remaining_calls(self):
        result = await self.create()
        self.api.optional_stats.side_effect = errors.RateLimitError("Rate limited", retry_after=10000)
        with self.assertRaises(UpdateFailed) as caught:
            await result._async_update_data()
        self.assertEqual(caught.exception.retry_after, 10000)
        self.assertEqual(self.api.optional_stats.await_count, 1)
        self.api.income_history.assert_not_awaited()

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
        self.assertIn("The pause could not be saved", str(caught.exception))
        self.api.profile.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
