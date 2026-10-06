"""Building Device Manager parameter sections from Doover settings."""

import pytest

from processor.dm_sections import (
    CURRENT_LOOP_ACTION_1,
    CURRENT_LOOP_CARD,
    MODBUS_ACTION_1,
    RS1_CARD,
    TASK_1,
    HawkSettings,
    ModbusRegister,
    ModbusSensor,
    TrackerSettings,
    build_hawk_plan,
    build_tracker_sections,
    sections_to_push,
    supported_sections,
)


def hawk(**kwargs):
    return HawkSettings(
        **{"card": "RS1", "read_period_mins": 240, "upload_every": 1, "sensor_power": "12V", "warm_up_s": 10, **kwargs}
    )


def register(address, **kwargs):
    return ModbusRegister(**{"function": 3, "address": address, "datatype": 0, "byte_order": 0, **kwargs})


def test_rs1_current_loop_matches_hand_configured_hawk():
    # Hawk 1960033 was set up by hand in Device Manager like this.
    plan = build_hawk_plan(hawk(current_loop_inputs=[1]))

    assert plan.analogues == {5: "4-20mA input 1"}
    assert plan.sections[CURRENT_LOOP_ACTION_1] == {
        "bPowerOnDelaySecs": "10",
        "bAnalogOffset": "5",
        "bPortNumber1": "1",
        "bPortNumber2": "0",
        "bPortNumber3": "0",
        "bPortNumber4": "0",
    }
    assert plan.sections[RS1_CARD]["fVboost12V"] == "1"
    assert plan.sections[RS1_CARD]["fCurrentLoopVboost"] == "1"
    assert plan.sections[RS1_CARD]["fModbusVboost"] == "0"
    assert plan.sections[TASK_1]["iEventPeriod"] == "240"
    assert plan.sections[TASK_1]["iAction1"] == "80"
    assert plan.sections[TASK_1]["iAction2"] == "0"


def test_modbus_registers_follow_current_loop_analogues():
    plan = build_hawk_plan(hawk(
        current_loop_inputs=[1],
        modbus_sensors=[
            ModbusSensor(address=3, registers=[register(100, datatype=4), register(102)]),
            ModbusSensor(address=7, registers=[register(0, function=4)]),
        ],
    ))

    assert list(plan.analogues) == [5, 6, 7, 8]
    first, second = plan.sections[MODBUS_ACTION_1], plan.sections[MODBUS_ACTION_1 + 1]
    assert first["bAddress"] == "3"
    assert first["bAnalogOffset"] == "6"
    assert (first["iR1RegisterAddress"], first["bR1Datatype"]) == ("100", "4")
    assert first["bR3Function"] == "0"  # unused readings are switched off
    assert second["bAnalogOffset"] == "8"
    assert second["bR1Function"] == "4"
    assert [plan.sections[TASK_1][f"iAction{i}"] for i in range(1, 4)] == ["80", "160", "161"]


def test_current_loop_card_powers_only_the_inputs_read():
    plan = build_hawk_plan(hawk(card="4-20mA", sensor_power="5V", current_loop_inputs=[2, 4]))

    assert plan.analogues == {5: "4-20mA input 2", 6: "4-20mA input 4"}
    assert plan.sections[CURRENT_LOOP_CARD] == {
        "fVboost12V": "0",
        "fVboostAlwaysOn": "0",
        "f420mA1_Vboost": "0",
        "f420mA2_Vboost": "1",
        "f420mA3_Vboost": "0",
        "f420mA4_Vboost": "1",
    }
    assert RS1_CARD not in plan.sections


def test_sensors_always_on_keeps_vboost_on_for_either_card():
    assert build_hawk_plan(hawk(current_loop_inputs=[1], sensors_always_on=True)).sections[RS1_CARD]["fVboostAlwaysOn"] == "1"
    plan = build_hawk_plan(hawk(card="4-20mA", current_loop_inputs=[1], sensors_always_on=True))
    assert plan.sections[CURRENT_LOOP_CARD]["fVboostAlwaysOn"] == "1"


def test_externally_powered_sensors_leave_vboost_off():
    plan = build_hawk_plan(hawk(sensor_power="External", current_loop_inputs=[1]))
    assert plan.sections[RS1_CARD]["fCurrentLoopVboost"] == "0"


def test_nothing_configured_pushes_nothing():
    assert build_hawk_plan(hawk()).sections == {}


@pytest.mark.parametrize("settings, message", [
    (dict(current_loop_inputs=[2]), "only has 4-20mA inputs 1-1"),
    (dict(card="4-20mA", modbus_sensors=[ModbusSensor(address=1, registers=[register(0)])]), "need the RS1 card"),
    (dict(modbus_sensors=[ModbusSensor(address=1, registers=[])]), "needs 1-8 registers"),
    (dict(modbus_sensors=[ModbusSensor(address=i, registers=[register(0)]) for i in range(6)]), "up to 5"),
    (
        dict(modbus_sensors=[ModbusSensor(address=i, registers=[register(r) for r in range(8)]) for i in range(3)]),
        "only analogues 5-20",
    ),
    (
        dict(current_loop_inputs=[1], modbus_sensors=[ModbusSensor(address=i, registers=[register(0)]) for i in range(5)]),
        "Task 1 can run 5 actions",
    ),
])
def test_invalid_hawk_settings(settings, message):
    with pytest.raises(ValueError, match=message):
        build_hawk_plan(hawk(**settings))


def tracker(**kwargs):
    return TrackerSettings(**{
        "heartbeat_mins": 30,
        "log_odometer": True,
        "run_detect": True,
        "run_detect_on_v": 13.2,
        "run_detect_off_v": 13.1,
        "analogue_input": True,
        **kwargs,
    })


def test_tracker_sections_match_doover_default_bolt2():
    sections = build_tracker_sections(tracker())
    # What the "Doover Default Bolt2" template leaves on a device, as read back from DM.
    current = {
        1100: {"Heartbeat_Period": "30", "fAvoidGpsWander": "1"},
        15000: {
            "fLogDeviceOdoHours": "1",
            "fLogTripOdoHours": "0",
            "fAlwaysLogDeviceOdoHours": "1",
            "fAlwaysLogTripOdoHours": "0",
        },
        4000: {
            "RD_High_Voltage": "13.20",
            "RD_Low_Voltage": "13.10",
            "RD_Digital_Input": "0",
            "RD_Start_Time": "5",
            "RD_End_Time": "20",
        },
    }
    defaults = {2400: {"Analog_Input": "5"}}
    assert sections_to_push(sections, current, defaults) == {}
    # An unset section is at its defaults, so turning the input off is a change.
    off = build_tracker_sections(tracker(analogue_input=False))
    assert sections_to_push(off, current, defaults) == {2400: {"Analog_Input": "0"}}


def test_tracker_without_run_detect_disables_it():
    assert build_tracker_sections(tracker(run_detect=False))[4000] == {
        "RD_High_Voltage": "0",
        "RD_Low_Voltage": "0",
        "RD_Digital_Input": "255",
    }


def test_run_detect_thresholds_must_be_ordered():
    with pytest.raises(ValueError, match="lower"):
        build_tracker_sections(tracker(run_detect_on_v=12.0, run_detect_off_v=12.5))


def test_only_differences_are_pushed_unless_unreadable():
    desired = {1: {"a": "1"}, 2: {"b": "2"}}
    assert sections_to_push(desired, None, {}) == desired
    assert sections_to_push(desired, {1: {"a": "1", "x": "9"}, 2: {"b": "2"}}, {}) == {}


def test_sections_need_every_param_to_be_supported():
    desired = build_tracker_sections(tracker())
    # A Yabby reuses id 1100 for GPS settings and has no run detect or analogue input.
    yabby = {1100: {"bGpsTimeoutMinSec": "60"}, 15000: dict.fromkeys(desired[15000], "0")}
    supported, skipped = supported_sections(desired, yabby)
    assert set(supported) == {15000}
    assert skipped == [1100, 2400, 4000]
