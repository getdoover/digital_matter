from typing import Any

from pydoover.processor import run_app

from .application import G62Processor


def handler(event: dict[str, Any], context):
    """Lambda handler entry point."""
    run_app(
        G62Processor(),
        event,
        context,
    )
