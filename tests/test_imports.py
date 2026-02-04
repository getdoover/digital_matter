"""
Basic tests for the Digital Matter integration.

This ensures all modules are importable and that the config is valid.
"""


def test_import_integration():
    from integration.application import DigitalMatterIntegration
    assert DigitalMatterIntegration


def test_import_processor():
    from processor.application import DigitalMatterProcessor
    assert DigitalMatterProcessor


def test_integration_config():
    from integration.app_config import DigitalMatterIntegrationConfig

    config = DigitalMatterIntegrationConfig()
    assert isinstance(config.to_dict(), dict)


def test_processor_config():
    from processor.app_config import DigitalMatterProcessorConfig

    config = DigitalMatterProcessorConfig()
    assert isinstance(config.to_dict(), dict)


def test_processor_ui():
    from processor.app_ui import DigitalMatterUI

    ui = DigitalMatterUI()
    assert ui.fetch()


def test_parse_dm_record():
    from integration.application import parse_dm_record, get_uplink_reason

    # Test uplink reason translation
    assert get_uplink_reason(1) == "Start of trip"
    assert get_uplink_reason(11) == "Heartbeat"
    assert "Unknown" in get_uplink_reason(999)

    # Test record parsing
    record = {
        "Reason": 11,
        "DateUTC": "2024-01-01T12:00:00Z",
        "SeqNo": 123,
        "Fields": [
            {"FType": 0, "Lat": -33.8688, "Long": 151.2093, "Alt": 50, "Spd": 1500, "PosAcc": 5},
            {"FType": 2, "DIn": 1},
            {"FType": 6, "AnalogueData": {"1": 3800, "2": 1350, "3": 2500, "4": 20}},
            {"FType": 27, "Odo": 10000000, "RH": 360000},
        ],
    }

    parsed = parse_dm_record(record)

    assert parsed["uplink_reason"] == "Heartbeat"
    assert parsed["uplink_reason_code"] == 11
    assert parsed["device_time_utc"] == "2024-01-01T12:00:00Z"
    assert parsed["sequence_number"] == 123

    # GPS data
    assert parsed["position"]["lat"] == -33.8688
    assert parsed["position"]["long"] == 151.2093
    assert parsed["speed_kmh"] == 1500 * 0.036  # 54 km/h
    assert parsed["gps_accuracy_m"] == 5

    # Digital inputs
    assert parsed["ignition_on"] is True

    # Analogue data
    assert parsed["battery_voltage"] == 3.8
    assert parsed["system_voltage"] == 13.5
    assert parsed["device_temp_c"] == 25.0
    assert parsed["signal_strength_percent"] == round(20 * (100 / 31))

    # Odometer and run hours
    assert parsed["odometer_km"] == 100.0
    assert parsed["run_hours"] == 100.0
