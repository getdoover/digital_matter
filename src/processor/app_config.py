from enum import Enum
from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig, SerialNumberConfig


class DeviceType(Enum):
    vehicle_tracker = "Vehicle Tracker"
    general = "General"


class ModbusRegisterConfig(config.Object):
    register_type = config.Enum("Register Type", choices=["Holding", "Input"], default="Holding")
    address = config.Integer("Register Address", minimum=0, maximum=65535)
    data_type = config.Enum(
        "Data Type",
        choices=["UINT16", "INT16", "UINT32", "INT32", "Float32", "Float64"],
        default="UINT16",
    )
    byte_order = config.Enum(
        "Byte Order",
        choices=["ABCD", "DCBA", "CDAB", "BADC"],
        default="ABCD",
        description="ABCD is big endian, the Modbus standard.",
    )
    scale_exponent = config.Integer(
        "Scale Exponent",
        default=0,
        minimum=-9,
        maximum=9,
        description="Multiply the reading by 10^x before storing it, as the Hawk stores whole numbers. "
        "E.g. 1 stores 12.3 as 123.",
    )


class ModbusSensorConfig(config.Object):
    address = config.Integer("Device Address", default=1, minimum=1, maximum=247)
    registers = config.Array(
        "Registers",
        element=ModbusRegisterConfig("Register"),
        min_items=1,
        max_items=8,
        description="Each register is stored in the next free analogue.",
    )


class DigitalMatterProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_dm_event", "ui_cmds"], advanced=True)
    position = config.ApplicationPosition()
    default_open = config.ApplicationDefaultOpen(default=True)

    serial_number = SerialNumberConfig(
        description="Digital Matter Serial Number",
    )

    device_type = config.Enum(
        "Device Type",
        choices=DeviceType,
        default=DeviceType.vehicle_tracker,
        description="Vehicle trackers (e.g. G62/G70) show GPS, ignition, odometer and run hours. "
        "General devices (e.g. Hawk) show their analogue and digital inputs instead, detected automatically.",
    )

    odometer_offset_km = config.Number(
        "Odometer Offset (km)",
        description="Offset to add to the device odometer reading",
        default=0.0,
        show_if=config.equal(device_type, DeviceType.vehicle_tracker),
    )

    run_hours_offset = config.Number(
        "Run Hours Offset",
        description="Offset to add to the device run hours reading",
        default=0.0,
        show_if=config.equal(device_type, DeviceType.vehicle_tracker),
    )

    # Device Manager config, pushed to the device on deployment. Settings are
    # flat rather than grouped in objects so installs that predate them still
    # load with defaults, and only shown while Manage Device Config is on.
    manage_device_config = config.Boolean(
        "Manage Device Config",
        default=False,
        description="Push the device settings below to Device Manager on each deployment. "
        "Leave off to manage the device in Device Manager directly.",
    )
    _managed_tracker = config.all_of(
        manage_device_config, config.equal(device_type, DeviceType.vehicle_tracker)
    )
    _managed_general = config.all_of(manage_device_config, config.equal(device_type, DeviceType.general))

    heartbeat_mins = config.Integer(
        "Heartbeat Period (minutes)",
        default=30,
        minimum=1,
        maximum=2880,
        description="Longest the tracker goes without reporting in.",
        show_if=_managed_tracker,
    )
    log_odometer = config.Boolean(
        "Report Odometer and Run Hours",
        default=True,
        description="Device Manager has this off by default, which leaves odometer and run hours blank.",
        show_if=_managed_tracker,
    )
    run_detect = config.Boolean(
        "Detect Running From Supply Voltage",
        default=False,
        description="Treat supply voltage above a threshold as ignition on. "
        "For gensets and machines without an ignition wire.",
        show_if=_managed_tracker,
    )
    run_detect_on_v = config.Number(
        "Running Above (V)",
        default=13.2,
        description="Used when detecting running from supply voltage.",
        show_if=_managed_tracker,
    )
    run_detect_off_v = config.Number(
        "Stopped Below (V)",
        default=13.1,
        description="Used when detecting running from supply voltage.",
        show_if=_managed_tracker,
    )
    analogue_input = config.Boolean(
        "Enable Analogue Input",
        default=True,
        description="Report the analogue input wire (G70 and similar). Ignored on trackers without one.",
        show_if=_managed_tracker,
    )

    hawk_card = config.Enum(
        "Expansion Card",
        choices=["RS1", "4-20mA"],
        default="RS1",
        description="RS1 has one 4-20mA input plus RS485 Modbus. The 4-20mA card has four 4-20mA inputs.",
        show_if=_managed_general,
    )
    read_period_mins = config.Integer(
        "Read Period (minutes)",
        default=60,
        minimum=2,
        description="How often the sensors are read. With Upload Every N Reads this sets the update interval. "
        "Updating more often than hourly significantly shortens battery life; "
        "use the Fast Updates button for short bursts instead.",
        show_if=_managed_general,
    )
    upload_every = config.Integer(
        "Upload Every N Reads",
        default=1,
        minimum=1,
        maximum=255,
        description="Readings are logged every read and uploaded in batches of this many.",
        show_if=_managed_general,
    )
    sensor_power = config.Enum(
        "Sensor Power",
        choices=["12V", "5V", "External"],
        default="12V",
        description="Power the sensors from the Hawk's boosted output while reading, or leave them externally powered.",
        show_if=_managed_general,
    )
    warm_up_s = config.Integer(
        "Sensor Warm Up (s)",
        default=1,
        minimum=0,
        maximum=255,
        description="Time to power sensors before reading.",
        show_if=_managed_general,
    )
    current_loop_inputs = config.Array(
        "4-20mA Inputs",
        name="current_loop_inputs",
        element=config.Integer("Input", minimum=1, maximum=4),
        default=[],
        unique_items=True,
        description="Inputs to read (1 on the RS1 card, 1-4 on the 4-20mA card). "
        "They're stored from analogue 5 up, in µA.",
        show_if=_managed_general,
    )
    modbus_baud_rate = config.Enum(
        "Modbus Baud Rate",
        choices=["1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600", "115200"],
        default="9600",
        show_if=_managed_general,
    )
    modbus_parity = config.Enum(
        "Modbus Parity",
        choices=["None", "Even", "Odd"],
        default="Even",
        show_if=_managed_general,
    )
    modbus_sensors = config.Array(
        "Modbus Sensors",
        element=ModbusSensorConfig("Modbus Sensor"),
        default=[],
        max_items=5,
        description="RS485 Modbus RTU sensors (RS1 card only). Their registers are stored after the 4-20mA inputs.",
        show_if=_managed_general,
    )

    dm_api_key = config.String(
        "Device Manager API Key",
        default="",
        advanced=True,
        show_if=manage_device_config,
        description="Digital Matter Device Manager API key, needed to manage device config. "
        "Set it in the organisation's config profile rather than per device.",
    )

    hide_ui = config.Boolean(
        "Hide Default UI",
        description="Whether to hide the default UI. Useful if you have a custom UI application.",
        default=False,
        advanced=True,
    )

    @property
    def is_vehicle_tracker(self) -> bool:
        return self.device_type.value is DeviceType.vehicle_tracker


def export():
    DigitalMatterProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )
