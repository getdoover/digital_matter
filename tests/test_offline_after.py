"""Offline After: how long after a report a device is called offline."""

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
