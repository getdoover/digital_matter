from pydoover.tags import Tag, Tags

from .app_config import DigitalMatterProcessorConfig, analogue_tag_name


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

    async def setup(self):
        # One scaled-value tag per configured analogue input (general devices).
        if self.config is None or self.config.is_vehicle_tracker:
            return
        # A slot listed twice shares one tag rather than failing setup.
        numbers = {i.analogue_number.value for i in self.config.analogue_inputs.elements}
        for number in sorted(numbers):
            self.add_tag(analogue_tag_name(number), Tag("number", default=None))
