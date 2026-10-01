"""Vehicle tracker vs general (e.g. Hawk 4-20mA) device type behaviour."""

import asyncio

from integration.application import decode_bits, parse_dm_record
from processor.app_config import DeviceType, DigitalMatterProcessorConfig
from processor.app_tags import DigitalMatterTags, detect_inputs
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


GENERAL = {"device_type": "General"}


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
    assert "battery_voltage" in names
    assert not any(n.startswith(("analogue_", "digital_input_")) for n in names)


def test_detected_inputs_added_to_ui():
    config = make_config(**GENERAL)
    tags = DigitalMatterTags("digital_matter_processor_1", None, config)
    asyncio.run(tags.setup())
    ui = DigitalMatterUI(config, tags, "digital_matter_processor_1")
    asyncio.run(ui.setup())

    detected = {"analogue": [5, 11], "digital": [3]}
    tags.add_input_tags(detected)
    ui.add_input_elements(detected)
    # Re-adding the same inputs is a no-op rather than a duplicate-tag error.
    tags.add_input_tags(detected)
    ui.add_input_elements(detected)

    assert ui.analogue_5.display_name == "Analogue 5"
    assert ui.digital_input_3.display_name == "Digital Input 3"
    children = ui.to_schema(resolve_config=False)["children"]
    assert {"analogue_5", "analogue_11", "digital_input_3"} <= set(children)


def test_detect_inputs():
    parsed = parse_dm_record({
        "Fields": [
            {"FType": 2, "DIn": 8, "DOut": 0},
            {"FType": 6, "AnalogueData": {"1": 0, "2": 692, "3": 2500, "4": 14, "5": 0}},
        ]
    })
    assert detect_inputs(parsed) == {"analogue": [5], "digital": [3]}


def test_decode_bits():
    assert decode_bits(8) == {str(i): i == 3 for i in range(8)}
    assert decode_bits(1 << 9)["9"] is True


def test_unknown_fields_forwarded():
    modbus = {"FType": 99, "Data": [1, 2, 3]}
    parsed = parse_dm_record({"Fields": [modbus, {"FType": 2, "DIn": 0}]})
    assert parsed["fields"]["99"] == [modbus]
    assert parsed["fields"]["2"] == [{"FType": 2, "DIn": 0}]


def test_int32_analogues_forwarded():
    parsed = parse_dm_record({
        "Fields": [
            {"FType": 6, "AnalogueData": {"1": 3800, "5": 1234}},
            {"FType": 7, "AnalogueData": {"11": 12000}},
        ]
    })
    assert parsed["analogue_raw"] == {"1": 3800, "5": 1234, "11": 12000}
