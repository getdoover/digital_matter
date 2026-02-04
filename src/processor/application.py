import logging
from datetime import datetime, timezone, timedelta

from pydoover.cloud.processor import (
    Application,
    MessageCreateEvent,
)
from pydoover.cloud.processor.types import ConnectionStatus
from pydoover.ui import ApplicationVariant

from .app_config import DigitalMatterProcessorConfig
from .app_ui import DigitalMatterUI


log = logging.getLogger(__name__)


class DigitalMatterProcessor(Application):
    config: DigitalMatterProcessorConfig

    async def setup(self):
        self.ui = DigitalMatterUI()
        self.ui_manager.add_children(*self.ui.fetch())
        self.ui_manager.set_variant(ApplicationVariant.stacked)

    async def on_message_create(self, event: MessageCreateEvent):
        """
        Handle incoming Digital Matter events forwarded from the integration.

        The integration parses the raw payload and forwards normalized data
        to the `on_dm_event` channel on each device agent.
        """
        if event.channel_name != "on_dm_event":
            return

        data = event.message.data
        log.info(f"Processing Digital Matter event: {data}")

        # Update UI with telemetry data
        self.ui.update(
            data,
            odometer_offset=self.config.odometer_offset_km.value or 0.0,
            run_hours_offset=self.config.run_hours_offset.value or 0.0,
        )

        # Update status display and icon
        display_string, status_icon = self.ui.get_status_display(data)
        self.ui_manager.set_display_string(display_string)
        if status_icon:
            self.ui_manager.set_status_icon(status_icon)

        # Publish location to the location channel if we have a valid position
        position = data.get("position")
        if position is not None:
            await self.api.publish_message(
                self.agent_id,
                "location",
                position
            )

        # Update connection status
        # Digital Matter devices typically report periodically (e.g., every 10-30 minutes)
        # Set offline threshold to 1 hour from now
        await self.ping_connection(
            online_at=datetime.now(timezone.utc),
            connection_status=ConnectionStatus.periodic_unknown,
            offline_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Push UI updates to connected clients
        await self.ui_manager.push_async()
