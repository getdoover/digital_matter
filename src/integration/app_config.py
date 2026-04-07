from pathlib import Path

from pydoover import config
from pydoover.processor import IngestionEndpointConfig, ExtendedPermissionsConfig


class DigitalMatterIntegrationConfig(config.Schema):
    integration = IngestionEndpointConfig()
    permissions = ExtendedPermissionsConfig()


def export():
    DigitalMatterIntegrationConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_integration"
    )
