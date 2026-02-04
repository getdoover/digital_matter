from typing import Any

from pydoover.cloud.processor import run_app

from .application import DigitalMatterIntegration
from .app_config import DigitalMatterIntegrationConfig


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    DigitalMatterIntegrationConfig.clear_elements()
    run_app(
        DigitalMatterIntegration(config=DigitalMatterIntegrationConfig()),
        event,
        context,
    )
