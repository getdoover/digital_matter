from pydoover.tags import Tag, Tags


class DigitalMatterTags(Tags):
    run_hours = Tag("number", default=None)
    odometer_km = Tag("number", default=None)

    speed = Tag("number", default=None)
    gps_accuracy = Tag("number", default=None)
    ignition_on = Tag("boolean", default=None)
    system_voltage = Tag("number", default=None)
    battery_voltage = Tag("number", default=None)
    signal_strength = Tag("number", default=None)
    device_temp = Tag("number", default=None)
    uplink_reason = Tag("string", default=None)
    device_time = Tag("string", default=None)
