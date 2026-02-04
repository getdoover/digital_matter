from pathlib import Path

from pydoover import config
from pydoover.cloud.processor import IngestionEndpointConfig, ExtendedPermissionsConfig


class DigitalMatterIntegrationConfig(config.Schema):
    def __init__(self):
        self.integration = IngestionEndpointConfig()
        self.permissions = ExtendedPermissionsConfig()


def export():
    DigitalMatterIntegrationConfig().export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_integration"
    )


if __name__ == "__main__":
    export()
