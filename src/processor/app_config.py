from enum import Enum
from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig, SerialNumberConfig


class DeviceType(Enum):
    vehicle_tracker = "Vehicle Tracker"
    general = "General"


class AnalogueInputConfig(config.Object):
    """One sensor wired into a Digital Matter analogue slot (e.g. a Hawk 4-20mA input).

    The device writes each sensor reading into a numbered "Analog" slot chosen in
    the Digital Matter device config. We linearly map the raw slot value onto the
    engineering range, so the same scaling works for 4-20mA and voltage inputs.
    """

    name = config.String(
        "Name",
        description="Display name for this input, e.g. 'Tank Level'.",
    )
    analogue_number = config.Integer(
        "Analogue Number",
        default=5,
        minimum=5,
        maximum=50,
        description=(
            "The Digital Matter 'Analog' slot this sensor is written to in the device config. "
            "1-4 are reserved for battery, supply voltage, temperature and signal."
        ),
    )
    raw_min = config.Number(
        "Raw Min",
        default=4000.0,
        description="Raw value the device reports at the bottom of the sensor range (e.g. 4mA).",
    )
    raw_max = config.Number(
        "Raw Max",
        default=20000.0,
        description="Raw value the device reports at the top of the sensor range (e.g. 20mA).",
    )
    scaled_min = config.Number(
        "Scaled Min",
        default=0.0,
        description="Engineering value at Raw Min.",
    )
    scaled_max = config.Number(
        "Scaled Max",
        default=100.0,
        description="Engineering value at Raw Max.",
    )
    units = config.String("Units", default="%")
    precision = config.Integer("Decimal Places", default=1, minimum=0, maximum=6)

    def scale(self, raw: float) -> float:
        raw_min, raw_max = self.raw_min.value, self.raw_max.value
        scaled_min, scaled_max = self.scaled_min.value, self.scaled_max.value
        if raw_max == raw_min:
            return scaled_min
        return scaled_min + (raw - raw_min) * (scaled_max - scaled_min) / (raw_max - raw_min)


class DigitalMatterProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_dm_event"], advanced=True)
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
        "General devices (e.g. Hawk) show configurable analogue inputs instead.",
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

    analogue_inputs = config.Array(
        "Analogue Inputs",
        element=AnalogueInputConfig("Analogue Input"),
        default=[],
        description="Sensors wired into the device's analogue slots, e.g. 4-20mA inputs on a Hawk.",
        show_if=config.equal(device_type, DeviceType.general),
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


def analogue_tag_name(analogue_number: int) -> str:
    return f"analogue_{analogue_number}"


def export():
    DigitalMatterProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )
