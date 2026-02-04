from pathlib import Path

from pydoover import config
from pydoover.cloud.processor import ManySubscriptionConfig


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


def export():
    DigitalMatterProcessorConfig().export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )


if __name__ == "__main__":
    export()
