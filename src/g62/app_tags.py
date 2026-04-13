from pydoover.tags import Tag, Tags


class G62Tags(Tags):
    # Trip / status flags
    trip_type = Tag("string", default=None)
    ext_power_good = Tag("boolean", default=None)
    gps_current = Tag("boolean", default=None)
    ignition = Tag("boolean", default=None)
    digital_input_1 = Tag("boolean", default=None)
    digital_input_2 = Tag("boolean", default=None)
    digital_output = Tag("boolean", default=None)

    # Position / motion
    heading_deg = Tag("number", default=None)
    speed_kmh = Tag("number", default=None)
    gps_accuracy_m = Tag("number", default=None)

    # Voltages / environment
    battery_v = Tag("number", default=None)
    external_v = Tag("number", default=None)
    analog_input_v = Tag("number", default=None)
    temperature_c = Tag("number", default=None)

    # Counters
    runtime_s = Tag("integer", default=None)
    odometer_km = Tag("number", default=None)

    # Downlink ack
    downlink_ack_seq = Tag("integer", default=None)
    downlink_ack_accepted = Tag("boolean", default=None)
    firmware_version = Tag("string", default=None)
