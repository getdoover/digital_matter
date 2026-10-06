"""Build Digital Matter Device Manager parameter sections from Doover settings.

Vehicle trackers map fairly directly onto DM sections. A Hawk reads sensors through a chain of DM parameter sections: Task 1 runs on
a schedule and triggers "actions" (a 4-20mA read, a Modbus read), each action
writes its readings into analogue slots, and the expansion card section powers
the sensors while they're read. This module turns the handful of settings a
user cares about into that chain.

Only the params we manage are sent; DM leaves every other param untouched.
"""

from dataclasses import dataclass, field

from .app_tags import FIRST_SENSOR_ANALOGUE

HAWK_PRODUCT_ID = 142

TASK_1 = 7000
RS1_CARD = 61186
CURRENT_LOOP_CARD = 61191
CURRENT_LOOP_ACTION_1 = 61520
MODBUS_ACTION_1 = 61600

# Codes Task 1's iActionN params use to name the action to run.
TASK_RUNS_CURRENT_LOOP_ACTION_1 = 80
TASK_RUNS_MODBUS_ACTION_1 = 160
TASK_ACTION_SLOTS = 5

MAX_MODBUS_SENSORS = 5
MAX_MODBUS_REGISTERS = 8
LAST_ANALOGUE = 20

PERIOD_UNIT_MINUTES = 2

# DM codes for the choices offered in the Doover config.
MODBUS_FUNCTION = {"Holding": 3, "Input": 4}
MODBUS_DATATYPE = {"UINT16": 0, "INT16": 1, "UINT32": 2, "INT32": 3, "Float32": 4, "Float64": 5}
MODBUS_BYTE_ORDER = {"ABCD": 0, "DCBA": 1, "CDAB": 2, "BADC": 3}
MODBUS_PARITY = {"None": 0, "Even": 1, "Odd": 2}

CARD_RS1 = "RS1"
CARD_CURRENT_LOOP = "4-20mA"
CURRENT_LOOP_INPUTS = {CARD_RS1: 1, CARD_CURRENT_LOOP: 4}

POWER_EXTERNAL = "External"
POWER_12V = "12V"


@dataclass
class ModbusRegister:
    function: int  # 3 = holding registers, 4 = input registers
    address: int
    datatype: int  # 0=UINT16, 1=INT16, 2=UINT32, 3=INT32, 4=float32, 5=float64
    byte_order: int  # 0=ABCD, 1=DCBA, 2=CDAB, 3=BADC
    scale_exponent: int = 0


@dataclass
class ModbusSensor:
    address: int
    registers: list[ModbusRegister]


@dataclass
class HawkSettings:
    card: str
    read_period_mins: int
    upload_every: int
    sensor_power: str
    warm_up_s: int
    current_loop_inputs: list[int] = field(default_factory=list)
    modbus_baud_rate: int = 9600
    modbus_parity: int = 1  # 0=None, 1=Even, 2=Odd
    modbus_sensors: list[ModbusSensor] = field(default_factory=list)
    # Keep the boost output on between reads, e.g. so a sensor can be
    # configured over Bluetooth.
    sensors_always_on: bool = False


@dataclass
class HawkPlan:
    # {section id: {param: value}}, values as strings like the DM API expects.
    sections: dict[int, dict[str, str]]
    # {analogue slot: what is read into it}, e.g. {5: "4-20mA input 1"}.
    analogues: dict[int, str]


def _flag(value: bool) -> str:
    return "1" if value else "0"


def build_hawk_plan(settings: HawkSettings) -> HawkPlan:
    """Work out the DM sections that make a Hawk read the configured sensors.

    4-20mA inputs fill analogues from 5 up, in input order, then each Modbus
    register takes the next free analogue.
    """
    inputs = sorted(set(settings.current_loop_inputs))
    max_input = CURRENT_LOOP_INPUTS[settings.card]
    if any(not 1 <= i <= max_input for i in inputs):
        raise ValueError(f"The {settings.card} card only has 4-20mA inputs 1-{max_input}, got {inputs}.")
    if settings.modbus_sensors and settings.card != CARD_RS1:
        raise ValueError(f"Modbus sensors need the {CARD_RS1} card, not the {settings.card} card.")
    if len(settings.modbus_sensors) > MAX_MODBUS_SENSORS:
        raise ValueError(f"A Hawk supports up to {MAX_MODBUS_SENSORS} Modbus sensors.")

    sections: dict[int, dict[str, str]] = {}
    analogues: dict[int, str] = {}
    task_actions: list[int] = []
    next_analogue = FIRST_SENSOR_ANALOGUE

    if inputs:
        sections[CURRENT_LOOP_ACTION_1] = {
            "bPowerOnDelaySecs": str(settings.warm_up_s),
            "bAnalogOffset": str(next_analogue),
            **{f"bPortNumber{i}": _flag(i in inputs) for i in range(1, 5)},
        }
        for i in inputs:
            analogues[next_analogue] = f"4-20mA input {i}"
            next_analogue += 1
        task_actions.append(TASK_RUNS_CURRENT_LOOP_ACTION_1)

    for n, sensor in enumerate(settings.modbus_sensors):
        if not 1 <= len(sensor.registers) <= MAX_MODBUS_REGISTERS:
            raise ValueError(
                f"Modbus sensor {n + 1} needs 1-{MAX_MODBUS_REGISTERS} registers, got {len(sensor.registers)}."
            )
        params = {
            "bAddress": str(sensor.address),
            "bPowerOnDelaySecs": str(settings.warm_up_s),
            "bAnalogOffset": str(next_analogue),
        }
        for r in range(1, MAX_MODBUS_REGISTERS + 1):
            reg = sensor.registers[r - 1] if r <= len(sensor.registers) else None
            params |= {
                f"bR{r}Function": str(reg.function if reg else 0),
                f"iR{r}RegisterAddress": str(reg.address if reg else 0),
                f"bR{r}Datatype": str(reg.datatype if reg else 0),
                f"fR{r}ByteOrder": str(reg.byte_order if reg else 0),
                f"fR{r}ScalingExponent": str(reg.scale_exponent if reg else 0),
            }
        sections[MODBUS_ACTION_1 + n] = params
        for reg in sensor.registers:
            analogues[next_analogue] = f"Modbus sensor {n + 1} (address {sensor.address}) register {reg.address}"
            next_analogue += 1
        task_actions.append(TASK_RUNS_MODBUS_ACTION_1 + n)

    if next_analogue - 1 > LAST_ANALOGUE:
        raise ValueError(
            f"{next_analogue - FIRST_SENSOR_ANALOGUE} readings configured, but only analogues "
            f"{FIRST_SENSOR_ANALOGUE}-{LAST_ANALOGUE} are available."
        )
    if len(task_actions) > TASK_ACTION_SLOTS:
        raise ValueError(
            f"Task 1 can run {TASK_ACTION_SLOTS} actions, but {len(task_actions)} are needed "
            "(one for 4-20mA plus one per Modbus sensor)."
        )
    if not task_actions:
        return HawkPlan(sections={}, analogues={})

    powered = settings.sensor_power != POWER_EXTERNAL
    if settings.card == CARD_RS1:
        sections[RS1_CARD] = {
            "fVboost12V": _flag(settings.sensor_power == POWER_12V),
            "fVboostAlwaysOn": _flag(settings.sensors_always_on),
            "fCurrentLoopVboost": _flag(powered and bool(inputs)),
            "fModbusVboost": _flag(powered and bool(settings.modbus_sensors)),
            "iModbusBaudrate": str(settings.modbus_baud_rate),
            "bModbusParity": str(settings.modbus_parity),
        }
    else:
        sections[CURRENT_LOOP_CARD] = {
            "fVboost12V": _flag(settings.sensor_power == POWER_12V),
            "fVboostAlwaysOn": _flag(settings.sensors_always_on),
            **{f"f420mA{i}_Vboost": _flag(powered and i in inputs) for i in range(1, 5)},
        }

    sections[TASK_1] = {
        "bPeriodUnit": str(PERIOD_UNIT_MINUTES),
        "iEventPeriod": str(settings.read_period_mins),
        "bUploadMultiplier": str(settings.upload_every),
        **{
            f"iAction{slot}": str(task_actions[slot - 1] if slot <= len(task_actions) else 0)
            for slot in range(1, TASK_ACTION_SLOTS + 1)
        },
    }
    return HawkPlan(sections=sections, analogues=analogues)


HEARTBEAT = 1100
RUN_DETECT = 4000
ODOMETER = 15000
ANALOGUE_INPUT = 2400

RUN_DETECT_SETS_IGNITION = 0
NO_INPUT = 255
TRACKER_ANALOGUE = 5  # the integration reports this slot as analog_input_v


@dataclass
class TrackerSettings:
    heartbeat_mins: int
    log_odometer: bool
    run_detect: bool
    run_detect_on_v: float
    run_detect_off_v: float
    analogue_input: bool


def build_tracker_sections(settings: TrackerSettings) -> dict[int, dict[str, str]]:
    """DM sections for a vehicle tracker (G70, Bolt2 and friends)."""
    if settings.run_detect and settings.run_detect_off_v >= settings.run_detect_on_v:
        raise ValueError("Run detect's 'stopped below' voltage must be lower than its 'running above' voltage.")

    return {
        HEARTBEAT: {"Heartbeat_Period": str(settings.heartbeat_mins)},
        # DM defaults these off, which leaves odometer and run hours unreported.
        ODOMETER: {
            "fLogDeviceOdoHours": _flag(settings.log_odometer),
            "fAlwaysLogDeviceOdoHours": _flag(settings.log_odometer),
        },
        # Run detect treats supply voltage above a threshold as ignition on,
        # for gensets and machines without an ignition wire.
        RUN_DETECT: {
            "RD_High_Voltage": f"{settings.run_detect_on_v:.2f}" if settings.run_detect else "0",
            "RD_Low_Voltage": f"{settings.run_detect_off_v:.2f}" if settings.run_detect else "0",
            "RD_Digital_Input": str(RUN_DETECT_SETS_IGNITION if settings.run_detect else NO_INPUT),
        },
        ANALOGUE_INPUT: {"Analog_Input": str(TRACKER_ANALOGUE if settings.analogue_input else 0)},
    }


def supported_sections(
    desired: dict[int, dict[str, str]], defaults: dict[int, dict[str, str]]
) -> tuple[dict[int, dict[str, str]], list[int]]:
    """Split the desired sections into those the product has, and the rest.

    Section ids aren't global (1100 is Heartbeat on a G70 but GPS settings on a
    Yabby), so a section only counts if the product has every param in it.
    """
    supported = {
        section_id: params
        for section_id, params in desired.items()
        if params.keys() <= defaults.get(section_id, {}).keys()
    }
    return supported, sorted(desired.keys() - supported.keys())


def sections_to_push(
    desired: dict[int, dict[str, str]],
    current: dict[int, dict[str, str]] | None,
    defaults: dict[int, dict[str, str]],
) -> dict[int, dict[str, str]]:
    """The desired sections that differ from what DM currently holds.

    ``current`` is None when the API can't read the device's parameters (e.g.
    Hawks), in which case everything is pushed. Otherwise it holds only the
    sections that have been set, with everything else at ``defaults``.
    """
    if current is None:
        return dict(desired)

    def differs(section_id, params):
        held = defaults.get(section_id, {}) | current.get(section_id, {})
        return any(held.get(k) != v for k, v in params.items())

    return {section_id: params for section_id, params in desired.items() if differs(section_id, params)}
