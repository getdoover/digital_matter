from pathlib import Path

from pydoover import config
from pydoover.processor import ManySubscriptionConfig


class G62ProcessorConfig(config.Schema):
    subscription = ManySubscriptionConfig(default=["on_tts_event"], hidden=True)
    position = config.ApplicationPosition()

    hide_ui = config.Boolean(
        "Hide Default UI",
        description="Whether to hide the default UI. Useful if you have a custom UI application.",
        default=False,
    )


def export():
    G62ProcessorConfig.export(
        Path(__file__).parents[2] / "doover_config.json",
        "g62_processor",
    )
