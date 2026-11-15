"""Offline After and Reporting Interval: what the device's connection config is told."""

import asyncio
from datetime import datetime, timedelta, timezone

from processor.app_config import DigitalMatterProcessorConfig

from .test_power_on import make_app

REPORTED = datetime(2026, 11, 14, 6, 10, tzinfo=timezone.utc)


def test_an_hour_unless_told_otherwise():
    # What it has always been, so installs that predate the setting are unchanged.
    assert make_app()._offline_at(REPORTED) == REPORTED + timedelta(hours=1)


def test_a_twice_daily_tracker_can_ride_out_a_missed_report():
    app = make_app(offline_after_minutes=1500)
    assert app._offline_at(REPORTED) == REPORTED + timedelta(hours=25)


def test_setting_is_offered_for_every_device_type():
    setting = DigitalMatterProcessorConfig.to_schema()["properties"]["offline_after_minutes"]
    assert (setting["default"], setting["minimum"]) == (60, 5)
    assert "show_if" not in setting and "x-show-if" not in setting


class FakeApi:
    """The connection aggregate as stored, and what was written to it."""

    def __init__(self, stored=None, fail=False):
        self.stored = stored
        self.fail = fail
        self.reads = 0
        self.writes = []

    async def fetch_channel_aggregate(self, channel_name):
        self.reads += 1
        if self.stored is None:
            raise LookupError("no aggregate")
        return type("Aggregate", (), {"data": self.stored})()

    async def update_channel_aggregate(self, channel_name, data, log_update=False):
        if self.fail:
            raise RuntimeError("write refused")
        self.writes.append((channel_name, data, log_update))


def make_connected_app(invocation_config, api, **config):
    app = make_app(**config)
    app.api = api
    app.agent_id = 42
    app._connection_config = invocation_config
    return app


WAIT = {"config": {"offline_after": 90_000}}


def test_a_device_with_no_connection_config_is_given_the_wait():
    # The platform decides offline from this config, and waits an hour without
    # one whatever the app is set to.
    for stored in (None, {}, {"status": {"status": "PeriodicUnknown"}}):
        app = make_connected_app({}, FakeApi(stored))
        asyncio.run(app._ensure_connection_config(90_000))
        assert app.api.writes == [("doover_connection", WAIT, True)]


def test_only_the_wait_is_written_to_a_config_the_invocation_was_not_given():
    # Nothing else in it is ours to change.
    stored = {"config": {"connection_type": "Periodic", "expected_interval": 1800, "offline_after": 3600}}
    app = make_connected_app({}, FakeApi(stored))
    asyncio.run(app._ensure_connection_config(90_000))
    assert app.api.writes == [("doover_connection", WAIT, True)]


def test_a_stored_wait_that_already_matches_is_not_written_again():
    app = make_connected_app({}, FakeApi({"config": {"offline_after": 90_000}}))
    asyncio.run(app._ensure_connection_config(90_000))
    assert app.api.writes == []


def test_a_config_that_came_with_the_invocation_is_left_to_the_ping():
    api = FakeApi({"config": {"offline_after": 3600}})
    app = make_connected_app({"offline_after": 3600}, api)
    asyncio.run(app._ensure_connection_config(90_000))
    assert (api.reads, api.writes) == (0, [])


def test_a_refused_write_does_not_stop_the_ping():
    app = make_connected_app({}, FakeApi({}, fail=True))
    asyncio.run(app._ensure_connection_config(90_000))  # logged, not raised
    assert app.api.writes == []


def test_the_reporting_interval_is_written_once_it_is_known():
    # Alongside the wait when there is no config at all...
    app = make_connected_app({}, FakeApi(None), reporting_interval_minutes=720)
    asyncio.run(app._ensure_connection_config(90_000))
    assert app.api.writes == [
        ("doover_connection", {"config": {"offline_after": 90_000, "expected_interval": 43_200}}, True)
    ]
    # ...and by itself into a config the ping is already keeping the wait of.
    api = FakeApi()
    app = make_connected_app({"offline_after": 90_000}, api, reporting_interval_minutes=720)
    asyncio.run(app._ensure_connection_config(90_000))
    assert (api.reads, api.writes) == (0, [("doover_connection", {"config": {"expected_interval": 43_200}}, True)])
    # Once it is there, nothing more is written.
    app = make_connected_app(
        {"offline_after": 90_000, "expected_interval": 43_200}, FakeApi(), reporting_interval_minutes=720
    )
    asyncio.run(app._ensure_connection_config(90_000))
    assert app.api.writes == []


def test_left_blank_the_interval_is_not_touched():
    stored = {"offline_after": 3600, "expected_interval": 1800}
    app = make_connected_app(stored, FakeApi())
    asyncio.run(app._ensure_connection_config(3600))
    assert app.api.writes == []


def test_a_managed_device_reports_as_often_as_its_own_settings_say():
    from .test_power_on import make_app

    assert make_app().config.reporting_interval_secs is None
    assert make_app(reporting_interval_minutes=720).config.reporting_interval_secs == 43_200
    tracker = make_app(manage_device_config=True, heartbeat_period_minutes=30, reporting_interval_minutes=720)
    assert tracker.config.reporting_interval_secs == 1800
    hawk = make_app(
        device_type="General", manage_device_config=True, read_period_minutes=60, upload_every_n_reads=4
    )
    assert hawk.config.reporting_interval_secs == 4 * 3600
