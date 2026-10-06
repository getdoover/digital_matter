import logging
from datetime import datetime, timezone, timedelta

import aiohttp
from pydoover import ui
from pydoover.processor import Application
from pydoover.models import DeploymentEvent, MessageCreateEvent, ConnectionStatus
from pydoover.tags import LogMode

from .app_config import DigitalMatterProcessorConfig
from .dm_api import DeviceManagerClient, DeviceManagerError
from .dm_sections import (
    HAWK_PRODUCT_ID,
    MODBUS_BYTE_ORDER,
    MODBUS_DATATYPE,
    MODBUS_FUNCTION,
    MODBUS_PARITY,
    HawkSettings,
    ModbusRegister,
    ModbusSensor,
    TrackerSettings,
    build_hawk_plan,
    build_tracker_sections,
    sections_to_push,
    supported_sections,
)
from .app_tags import (
    DigitalMatterTags,
    analogue_tag_name,
    detect_inputs,
    digital_tag_name,
)
from .app_ui import DigitalMatterUI


log = logging.getLogger(__name__)

HARDWARE_CHANNEL = "dv-hardware"

# A Fast Updates burst: the shortest interval a Hawk manages (an upload takes
# about 2 minutes), for long enough to commission or check a sensor.
FAST_UPDATE_MINS = 2
FAST_UPDATE_DURATION = timedelta(minutes=30)


class DigitalMatterProcessor(Application):
    config_cls = DigitalMatterProcessorConfig
    ui_cls = DigitalMatterUI
    tags_cls = DigitalMatterTags

    config: DigitalMatterProcessorConfig
    tags: DigitalMatterTags
    ui: DigitalMatterUI

    async def setup(self):
        # Log every value each uplink reports, even when unchanged, so a steady
        # reading (e.g. a dam level that hasn't moved) still shows in history.
        self.tag_manager.log_mode = LogMode.ONLY_SET

    async def on_deployment(self, event: DeploymentEvent):
        if self.config.manage_device_config.value:
            await self._push_device_config()

    @ui.handler("fast_updates")
    async def on_fast_updates(self, ctx, _value):
        # Buttons report the press by setting a value, so clear it to re-arm.
        await ctx.set_value(None)
        if self.config.is_vehicle_tracker or not self.config.manage_device_config.value:
            return

        # The device only picks the faster schedule up at its next uplink, so
        # the burst's timer starts then rather than now.
        log.info("Fast updates requested, starting at the next uplink.")
        await self.tags.fast_updates_pending.set(True)
        await self.tags.fast_updates_until.set(None)
        await self._push_device_config()

    def _fast_updates_until(self) -> datetime | None:
        until = self.tags.fast_updates_until.value
        return datetime.fromtimestamp(until / 1000, timezone.utc) if until else None

    def _fast_updates_active(self) -> bool:
        return bool(self.tags.fast_updates_pending.value) or self._fast_updates_until() is not None

    async def _update_fast_updates(self):
        """Run a Fast Updates burst's timer, called on each uplink.

        The uplink after the button press is when the device picks up the
        faster schedule, so the 30 minutes start then. Once they're up, the
        normal interval is pushed back, which the device picks up on its next
        check-in (every couple of minutes during a burst).
        """
        now = datetime.now(timezone.utc)
        if self.tags.fast_updates_pending.value:
            until = now + FAST_UPDATE_DURATION
            log.info(f"Fast updates applied, running until {until}")
            await self.tags.fast_updates_pending.set(False)
            await self.tags.fast_updates_until.set(int(until.timestamp() * 1000))
            return

        until = self._fast_updates_until()
        if until is None or now < until:
            return

        log.info("Fast updates finished, restoring the normal interval.")
        await self.tags.fast_updates_until.set(None)
        if not await self._push_device_config():
            # Try again on the next uplink.
            await self.tags.fast_updates_until.set(int(until.timestamp() * 1000))

    async def _push_device_config(self) -> bool:
        """Push the configured settings to Device Manager, where they differ.

        DM is the store of record: sections are compared with what DM holds and
        only changes are sent. Hawks can't be read back, so they always get the
        full set. Returns whether the push succeeded.
        """
        api_key = self.config.dm_api_key.value
        if not api_key:
            log.warning("Manage Device Config is on but no Device Manager API key is set.")
            await self.tags.dm_config_status.set("Not pushed: no Device Manager API key set")
            return False

        serial = self.config.serial_number.value
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                client = DeviceManagerClient(session, api_key)
                product_id = await client.lookup_product(serial)
                desired = self._desired_sections(product_id)

                defaults = await client.get_defaults(product_id)
                desired, skipped = supported_sections(desired, defaults)
                if skipped:
                    log.info(f"Product {product_id} doesn't support sections {skipped}, skipping them.")

                current = await client.get_parameters(product_id, serial)
                changed = sections_to_push(desired, current, defaults)
                if changed:
                    await client.set_parameters(product_id, serial, changed)
        except (DeviceManagerError, aiohttp.ClientError, ValueError) as e:
            log.error(f"Failed to push device config: {e}")
            await self.tags.dm_config_status.set(f"Failed: {e}")
            return False

        if changed:
            status = f"Queued {len(changed)} section(s), applied at the next check-in"
        else:
            status = "Up to date"
        log.info(f"Device config for {serial} (product {product_id}): {status}. Sections: {changed}")
        await self.tags.dm_config_status.set(status)
        return True

    def _desired_sections(self, product_id: int) -> dict[int, dict[str, str]]:
        c = self.config
        if c.is_vehicle_tracker:
            return build_tracker_sections(TrackerSettings(
                heartbeat_mins=c.heartbeat_mins.value,
                log_odometer=c.log_odometer.value,
                run_detect=c.run_detect.value,
                run_detect_on_v=c.run_detect_on_v.value,
                run_detect_off_v=c.run_detect_off_v.value,
                analogue_input=c.analogue_input.value,
            ))

        if product_id != HAWK_PRODUCT_ID:
            log.info(f"No device settings to manage for product {product_id}.")
            return {}

        fast = self._fast_updates_active()
        plan = build_hawk_plan(HawkSettings(
            card=c.hawk_card.value,
            read_period_mins=FAST_UPDATE_MINS if fast else c.read_period_mins.value,
            upload_every=1 if fast else c.upload_every.value,
            sensor_power=c.sensor_power.value,
            warm_up_s=c.warm_up_s.value,
            current_loop_inputs=[e.value for e in c.current_loop_inputs.elements],
            modbus_baud_rate=int(c.modbus_baud_rate.value),
            modbus_parity=MODBUS_PARITY[c.modbus_parity.value],
            modbus_sensors=[
                ModbusSensor(
                    address=s.address.value,
                    registers=[
                        ModbusRegister(
                            function=MODBUS_FUNCTION[r.register_type.value],
                            address=r.address.value,
                            datatype=MODBUS_DATATYPE[r.data_type.value],
                            byte_order=MODBUS_BYTE_ORDER[r.byte_order.value],
                            scale_exponent=r.scale_exponent.value,
                        )
                        for r in s.registers.elements
                    ],
                )
                for s in c.modbus_sensors.elements
            ],
        ))
        log.info(f"Hawk analogues: {plan.analogues}")
        return plan.sections

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

        if self.config.is_vehicle_tracker:
            await self._update_vehicle_tags(data)
        else:
            await self._update_inputs(data)

        # Update tags with telemetry data (UI is bound to these via tag_ref)
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

        await self._update_fast_updates()

    async def _update_vehicle_tags(self, data: dict):
        odometer_offset = self.config.odometer_offset_km.value
        run_hours_offset = self.config.run_hours_offset.value

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

        if "analog_input_v" in data:
            await self.tags.analog_input_v.set(data["analog_input_v"])

    async def _update_inputs(self, data: dict):
        """Report every sensor input the device sends, adding UI for new ones."""
        known = self.tags.detected_inputs.value or {}
        found = detect_inputs(data)
        detected = {
            kind: sorted(set(known.get(kind, [])) | set(numbers))
            for kind, numbers in found.items()
        }

        if detected != known:
            log.info(f"Detected new inputs: {detected} (was {known})")
            self.tags.add_input_tags(detected)
            self.ui.add_input_elements(detected)
            await self.tags.detected_inputs.set(detected)
            await self.publish_ui_schema()

        analogue_raw = data.get("analogue_raw", {})
        for number in found["analogue"]:
            await self.tags.get_tag(analogue_tag_name(number)).set(analogue_raw[str(number)])

        digital_inputs = data.get("digital_inputs", {})
        for number in detected["digital"]:
            if str(number) in digital_inputs:
                await self.tags.get_tag(digital_tag_name(number)).set(digital_inputs[str(number)])

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
