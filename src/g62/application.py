import base64
import logging

from pydoover.processor import Application
from pydoover.models import MessageCreateEvent

from .app_config import G62ProcessorConfig
from .app_tags import G62Tags
from .app_ui import G62UI
from . import decoder

log = logging.getLogger(__name__)


class G62Processor(Application):
    config_cls = G62ProcessorConfig
    ui_cls = G62UI
    tags_cls = G62Tags

    config: G62ProcessorConfig
    tags: G62Tags
    ui: G62UI

    async def on_message_create(self, event: MessageCreateEvent):
        if event.channel.name != "on_tts_event":
            return

        uplink = event.message.data.get("uplink_message")
        if not uplink:
            return

        port = uplink.get("f_port")
        frm = uplink.get("frm_payload")
        if port is None or not frm:
            return

        try:
            payload = base64.b64decode(frm)
        except Exception:
            log.exception("Failed to base64-decode frm_payload: %r", frm)
            return

        decoded = decoder.decode(payload, port)
        if not decoded:
            log.warning("G62 port=%s len=%s did not match any known message", port, len(payload))
            return

        log.info("G62 decoded: %s", decoded)
        await self.apply_decoded(decoded)

        if "latitude" in decoded and "longitude" in decoded:
            await self.api.create_message(
                "location",
                {"lat": decoded["latitude"], "lng": decoded["longitude"]},
            )

    async def apply_decoded(self, d: dict):
        mapping = {
            "trip_type": self.tags.trip_type,
            "ext_power_good": self.tags.ext_power_good,
            "gps_current": self.tags.gps_current,
            "ignition": self.tags.ignition,
            "digital_input_1": self.tags.digital_input_1,
            "digital_input_2": self.tags.digital_input_2,
            "digital_output": self.tags.digital_output,
            "heading_deg": self.tags.heading_deg,
            "speed_kmh": self.tags.speed_kmh,
            "gps_accuracy_m": self.tags.gps_accuracy_m,
            "battery_v": self.tags.battery_v,
            "external_v": self.tags.external_v,
            "analog_input_v": self.tags.analog_input_v,
            "temperature_c": self.tags.temperature_c,
            "runtime_s": self.tags.runtime_s,
            "odometer_km": self.tags.odometer_km,
        }
        for key, tag in mapping.items():
            if key in d:
                await tag.set(d[key])

        if d.get("_type") == "downlink_ack":
            await self.tags.downlink_ack_seq.set(d["sequence"])
            await self.tags.downlink_ack_accepted.set(d["accepted"])
            await self.tags.firmware_version.set(d["firmware_version"])
