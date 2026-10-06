"""Power On: temporarily keep a Hawk's sensors powered and read every couple of minutes."""

import asyncio
from datetime import datetime, timedelta, timezone

from processor.app_tags import DigitalMatterTags
from processor.application import POWER_ON_READ_MINS, DigitalMatterProcessor
from processor.dm_sections import HAWK_PRODUCT_ID, RS1_CARD, TASK_1
from .test_device_type import make_config, make_ui

MANAGED_HAWK = {"device_type": "General", "manage_device_config": True, "current_loop_inputs": [1]}


def make_app(**config):
    app = DigitalMatterProcessor.__new__(DigitalMatterProcessor)
    app.config = make_config(**config)
    app.tags = DigitalMatterTags("digital_matter_processor_1", None, app.config)
    asyncio.run(app.tags.setup())
    return app


def test_button_only_on_managed_hawks():
    assert "power_on" in make_ui(make_config(**MANAGED_HAWK))._elements
    assert "power_on" not in make_ui(make_config(device_type="General"))._elements
    assert "power_on" not in make_ui(make_config(manage_device_config=True))._elements


def test_button_name_matches_its_handler():
    # The handler is looked up by the published element name, not the attribute.
    ui = make_ui(make_config(**MANAGED_HAWK))
    assert "power_on" in ui.to_schema(resolve_config=False)["children"]
    assert DigitalMatterProcessor.on_power_on._rpc_method == "power_on"


def test_power_on_sits_below_digital_inputs():
    ui = make_ui(make_config(**MANAGED_HAWK))
    detected = {"analogue": [5], "digital": [1, 3, 9]}
    ui.tags.add_input_tags(detected)
    ui.add_input_elements(detected)
    children = ui.to_schema(resolve_config=False)["children"]
    last_digital = max(c["position"] for n, c in children.items() if n.startswith("digital_input_"))
    assert last_digital < children["power_on"]["position"] < children["power_on_until"]["position"]


def test_power_on_powers_sensors_and_speeds_up_reads():
    app = make_app(**MANAGED_HAWK, read_period_minutes=240, upload_every_n_reads=4)
    task = app._desired_sections(HAWK_PRODUCT_ID)[TASK_1]
    assert (task["iEventPeriod"], task["bUploadMultiplier"]) == ("240", "4")

    app._power_on_active = lambda: True
    task = app._desired_sections(HAWK_PRODUCT_ID)[TASK_1]
    assert (task["iEventPeriod"], task["bUploadMultiplier"]) == (str(POWER_ON_READ_MINS), "1")
    assert app._desired_sections(HAWK_PRODUCT_ID)[RS1_CARD]["fVboostAlwaysOn"] == "1"


class FakeTag:
    def __init__(self, value=None):
        self.value = value

    async def set(self, value):
        self.value = value


def test_burst_timer_starts_at_the_next_uplink():
    app = make_app(**MANAGED_HAWK)
    app.tags = type("Tags", (), {
        "power_on_pending": FakeTag(True),
        "power_on_until": FakeTag(),
        "power_on_status": FakeTag("Waiting for device to connect"),
        "power_on_hidden": FakeTag(False),
    })()
    pushes = []

    async def push():
        pushes.append(app._power_on_active())
        return True

    app._push_device_config = push

    # The uplink after the press starts the 30 minutes.
    asyncio.run(app._update_power_on())
    assert app.tags.power_on_pending.value is False
    assert app.tags.power_on_status.value == "On"
    until = app._power_on_until()
    assert timedelta(minutes=29) < until - datetime.now(timezone.utc) <= timedelta(minutes=30)
    assert pushes == []

    # Mid-burst uplinks change nothing.
    asyncio.run(app._update_power_on())
    assert app._power_on_until() == until and pushes == []

    # Once it's over, the normal schedule is pushed.
    app.tags.power_on_until.value = int((datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp() * 1000)
    asyncio.run(app._update_power_on())
    assert app.tags.power_on_until.value is None
    assert pushes == [False]
    assert app.tags.power_on_status.value == "Turning off at next check-in"
    assert app.tags.power_on_hidden.value is False

    # The next check-in picks up the normal config, so the status is hidden again.
    asyncio.run(app._update_power_on())
    assert app.tags.power_on_status.value is None
    assert app.tags.power_on_hidden.value is True
