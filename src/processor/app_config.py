from enum import Enum
from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig, SerialNumberConfig


class DeviceType(Enum):
    vehicle_tracker = "Vehicle Tracker"
    general = "General"


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
