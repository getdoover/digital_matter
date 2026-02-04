from typing import Any

from pydoover.cloud.processor import run_app

from .application import DigitalMatterProcessor
from .app_config import DigitalMatterProcessorConfig


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    DigitalMatterProcessorConfig.clear_elements()
    run_app(
        DigitalMatterProcessor(config=DigitalMatterProcessorConfig()),
        event,
        context,
    )
