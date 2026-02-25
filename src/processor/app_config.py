from pathlib import Path

from pydoover import config
from pydoover.cloud.processor import ManySubscriptionConfig, SerialNumberConfig


class DigitalMatterProcessorConfig(config.Schema):
    def __init__(self):
        self.subscription = ManySubscriptionConfig()

        self.odometer_offset_km = config.Number(
            "Odometer Offset (km)",
            description="Offset to add to the device odometer reading",
            default=0.0,
        )

        self.run_hours_offset = config.Number(
            "Run Hours Offset",
            description="Offset to add to the device run hours reading",
            default=0.0,
        )

        self.serial_number = SerialNumberConfig(
            description="Digital Matter Serial Number",
        )

        self.hide_ui = config.Boolean(
            "Hide Default UI",
            description="Whether to hide the default UI. Useful if you have a custom UI application.",
            default=False,
        )
        self.position = config.ApplicationPosition()


def export():
    DigitalMatterProcessorConfig().export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )


if __name__ == "__main__":
    export()
