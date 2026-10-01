"""Vehicle tracker vs general (e.g. Hawk 4-20mA) device type behaviour."""

import asyncio

from integration.application import parse_dm_record
from processor.app_config import DeviceType, DigitalMatterProcessorConfig
from processor.app_tags import DigitalMatterTags
from processor.app_ui import VEHICLE_ELEMENTS, DigitalMatterUI


def make_config(**data):
    config = DigitalMatterProcessorConfig()
    config._inject_deployment_config({"dv_serial_number": "123", **data})
    return config


def make_ui(config):
    tags = DigitalMatterTags("digital_matter_processor_1", None, config)
    asyncio.run(tags.setup())
    ui = DigitalMatterUI(config, tags, "digital_matter_processor_1")
    asyncio.run(ui.setup())
    return ui


GENERAL = {
    "device_type": "General",
    "analogue_inputs": [
        {
            "name": "Tank Level",
            "analogue_number": 11,
            "raw_min": 4000,
            "raw_max": 20000,
            "scaled_min": 0,
            "scaled_max": 5,
            "units": "m",
            "precision": 2,
        }
    ],
}


def test_schema_uses_show_if():
    schema = DigitalMatterProcessorConfig.to_schema()
    assert "Vehicle Tracker" in str(schema)
    assert "General" in str(schema)


def test_vehicle_tracker_is_default():
    config = make_config()
    assert config.device_type.value is DeviceType.vehicle_tracker
    names = set(make_ui(config)._elements)
    assert {"speed", "odometer", "run_hours"} <= names


def test_general_swaps_ui():
    config = make_config(**GENERAL)
    assert not config.is_vehicle_tracker
    ui = make_ui(config)
    names = set(ui._elements)
    assert not names & set(VEHICLE_ELEMENTS)
    assert "analogue_input_0" in names
    assert "battery_voltage" in ui.details._children
    assert "gps_accuracy" not in ui.details._children
    assert ui.analogue_input_0.display_name == "Tank Level"


def test_analogue_scaling():
    config = make_config(**GENERAL)
    (tank,) = config.analogue_inputs.elements
    assert tank.scale(4000) == 0
    assert tank.scale(12000) == 2.5
    assert tank.scale(20000) == 5


def test_int32_analogues_forwarded():
    parsed = parse_dm_record({
        "Fields": [
            {"FType": 6, "AnalogueData": {"1": 3800, "5": 1234}},
            {"FType": 7, "AnalogueData": {"11": 12000}},
        ]
    })
    assert parsed["analogue_raw"] == {"1": 3800, "5": 1234, "11": 12000}
