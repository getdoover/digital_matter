"""Fast Updates: temporarily read a Hawk every couple of minutes."""

import asyncio
from datetime import datetime, timedelta, timezone

from processor.app_tags import DigitalMatterTags
from processor.application import FAST_UPDATE_MINS, DigitalMatterProcessor
from processor.dm_sections import HAWK_PRODUCT_ID, TASK_1
from .test_device_type import make_config, make_ui

MANAGED_HAWK = {"device_type": "General", "manage_device_config": True, "current_loop_inputs": [1]}


def make_app(**config):
    app = DigitalMatterProcessor.__new__(DigitalMatterProcessor)
    app.config = make_config(**config)
    app.tags = DigitalMatterTags("digital_matter_processor_1", None, app.config)
    asyncio.run(app.tags.setup())
    return app


def test_button_only_on_managed_hawks():
    assert "fast_updates" in make_ui(make_config(**MANAGED_HAWK))._elements
    assert "fast_updates" not in make_ui(make_config(device_type="General"))._elements
    assert "fast_updates" not in make_ui(make_config(manage_device_config=True))._elements


def test_button_name_matches_its_handler():
    # The handler is looked up by the published element name, not the attribute.
    ui = make_ui(make_config(**MANAGED_HAWK))
    assert "fast_updates" in ui.to_schema(resolve_config=False)["children"]
    assert DigitalMatterProcessor.on_fast_updates._rpc_method == "fast_updates"


def test_fast_updates_override_the_read_schedule():
    app = make_app(**MANAGED_HAWK, read_period_minutes=240, upload_every_n_reads=4)
    task = app._desired_sections(HAWK_PRODUCT_ID)[TASK_1]
    assert (task["iEventPeriod"], task["bUploadMultiplier"]) == ("240", "4")

    app._fast_updates_until = lambda: datetime.now(timezone.utc) + timedelta(minutes=30)
    task = app._desired_sections(HAWK_PRODUCT_ID)[TASK_1]
    assert (task["iEventPeriod"], task["bUploadMultiplier"]) == (str(FAST_UPDATE_MINS), "1")
