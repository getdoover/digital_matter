import logging
from datetime import datetime, timezone, timedelta

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent, ConnectionStatus

from .app_config import DigitalMatterProcessorConfig
from .app_tags import DigitalMatterTags
from .app_ui import DigitalMatterUI


log = logging.getLogger(__name__)

HARDWARE_CHANNEL = "dv-hardware"


class DigitalMatterProcessor(Application):
    config_cls = DigitalMatterProcessorConfig
    ui_cls = DigitalMatterUI
    tags_cls = DigitalMatterTags

    config: DigitalMatterProcessorConfig
    tags: DigitalMatterTags
    ui: DigitalMatterUI

    async def on_message_create(self, event: MessageCreateEvent):
        """
        Handle incoming Digital Matter events forwarded from the integration.

        The integration parses the raw payload and forwards normalized data
        to the `on_dm_event` channel on each device agent.
        """
        if event.channel.name != "on_dm_event":
            return

        data = event.message.data
        log.info(f"Processing Digital Matter event: {data}")

        if data.get("sim_iccid"):
            await self._update_hardware_iccid(data["sim_iccid"])

        odometer_offset = self.config.odometer_offset_km.value
        run_hours_offset = self.config.run_hours_offset.value

        # Update tags with telemetry data (UI is bound to these via tag_ref)
        if "speed_kmh" in data:
            await self.tags.speed.set(data["speed_kmh"])

        if "gps_accuracy_m" in data:
            await self.tags.gps_accuracy.set(data["gps_accuracy_m"])

        if "ignition_on" in data:
            await self.tags.ignition_on.set(data["ignition_on"])

        if "run_hours" in data:
            await self.tags.run_hours.set(data["run_hours"] + run_hours_offset)

        if "odometer_km" in data:
            await self.tags.odometer_km.set(data["odometer_km"] + odometer_offset)

        if "system_voltage" in data:
            await self.tags.system_voltage.set(data["system_voltage"])

        if "battery_voltage" in data:
            await self.tags.battery_voltage.set(data["battery_voltage"])

        if "signal_strength_percent" in data:
            await self.tags.signal_strength.set(data["signal_strength_percent"])

        if "device_temp_c" in data:
            await self.tags.device_temp.set(data["device_temp_c"])

        if "uplink_reason" in data:
            await self.tags.uplink_reason.set(data["uplink_reason"])

        if "device_time_utc" in data:
            await self.tags.device_time.set(data["device_time_utc"])

        # Publish location to the location channel if we have a valid position
        position = data.get("position")
        if position is not None:
            await self.api.update_channel_aggregate("location", position, replace_data=True)
            await self.api.create_message("location", position)

        # Update connection status
        # Digital Matter devices typically report periodically (e.g., every 10-30 minutes)
        # Set offline threshold to 1 hour from now
        await self.ping_connection(
            online_at=datetime.now(timezone.utc),
            connection_status=ConnectionStatus.periodic_unknown,
            offline_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

    async def _update_hardware_iccid(self, iccid: str):
        """Publish the SIM ICCID to the dv-hardware channel like host_configurator.

        Only republishes when the ICCID changes, so a stable SIM doesn't spam
        the channel on every uplink. host_configurator writes both a message
        (historical record) and the channel aggregate (latest, queryable
        without scanning messages); we do the same with the single field we
        know about, merging into the aggregate so any other hardware fields are
        preserved.
        """
        if self.tags.sim_iccid.value == iccid:
            return

        log.info(f"Publishing SIM ICCID {iccid} to {HARDWARE_CHANNEL}")
        # Match host_configurator's snapshot shape: the SIM ICCID lives under
        # the top-level "modem" key as sim_iccid.
        snapshot = {"modem": {"sim_iccid": iccid}}
        await self.api.create_message(HARDWARE_CHANNEL, snapshot)
        await self.api.update_channel_aggregate(HARDWARE_CHANNEL, snapshot)
        await self.tags.sim_iccid.set(iccid)
