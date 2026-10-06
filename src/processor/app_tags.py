from pydoover.tags import Tag, Tags

from .app_config import DigitalMatterProcessorConfig

# Analog slots 1-4 are the tracker's own battery, supply voltage, temperature
# and signal; sensors are wired into 5 and up.
FIRST_SENSOR_ANALOGUE = 5


def analogue_tag_name(number: int) -> str:
    return f"analogue_{number}"


def digital_tag_name(number: int) -> str:
    return f"digital_input_{number}"


def detect_inputs(data: dict) -> dict[str, list[int]]:
    """Which sensor inputs an on_dm_event message reports.

    Every analogue slot from 5 up counts. A digital input only counts once it has
    been seen active, since the DIn bitmask always carries every bit whether or
    not anything is wired to it.
    """
    analogue = [
        int(k) for k in data.get("analogue_raw", {})
        if str(k).isdigit() and int(k) >= FIRST_SENSOR_ANALOGUE
    ]
    digital = [int(k) for k, v in data.get("digital_inputs", {}).items() if v]
    return {"analogue": sorted(analogue), "digital": sorted(digital)}


class DigitalMatterTags(Tags):
    config: DigitalMatterProcessorConfig

    run_hours = Tag("number", default=None)
    odometer_km = Tag("number", default=None)

    speed = Tag("number", default=None)
    gps_accuracy = Tag("number", default=None)
    ignition_on = Tag("boolean", default=None)
    system_voltage = Tag("number", default=None)
    battery_voltage = Tag("number", default=None)
    signal_strength = Tag("number", default=None)
    device_temp = Tag("number", default=None)
    analog_input_v = Tag("number", default=None)
    uplink_reason = Tag("string", default=None)
    device_time = Tag("string", default=None)

    sim_iccid = Tag("string", default=None)

    # Outcome of the last Device Manager config push, e.g. "Up to date".
    dm_config_status = Tag("string", default=None)

    # When a Fast Updates burst ends (ms since epoch); None when not in one.
    fast_updates_until = Tag("number", default=None)

    # Sensor inputs seen so far, {"analogue": [5, ...], "digital": [3, ...]}.
    # Drives the per-input tags and UI elements on general devices.
    detected_inputs = Tag("object", default=None)

    async def setup(self):
        if self.config is None or self.config.is_vehicle_tracker:
            return
        self.add_input_tags(self.detected_inputs.value or {})

    def add_input_tags(self, detected: dict):
        """Declare a tag for each detected input that doesn't have one yet."""
        for number in detected.get("analogue", []):
            if self.get(analogue_tag_name(number)) is None:
                self.add_tag(analogue_tag_name(number), Tag("number", default=None))
        for number in detected.get("digital", []):
            if self.get(digital_tag_name(number)) is None:
                self.add_tag(digital_tag_name(number), Tag("boolean", default=None))
