from pathlib import Path

from pydoover import ui

from .app_tags import G62Tags


class G62UI(ui.UI, hidden="$config.app().hide_ui"):
    # Speed gauge
    speed_kmh = ui.NumericVariable(
        "Speed",
        value=G62Tags.speed_kmh,
        units="km/h",
        precision=0,
        ranges=[
            ui.Range("Low", 0, 20, ui.Colour.blue, show_on_graph=True),
            ui.Range("Normal", 20, 80, ui.Colour.green, show_on_graph=True),
            ui.Range("Fast", 80, 120, ui.Colour.yellow, show_on_graph=True),
        ],
    )

    # GPS accuracy
    gps_accuracy_m = ui.NumericVariable(
        "GPS Accuracy",
        value=G62Tags.gps_accuracy_m,
        units="m",
        precision=0,
        ranges=[
            ui.Range("Good", 0, 15, ui.Colour.green, show_on_graph=True),
            ui.Range("OK", 15, 30, ui.Colour.blue, show_on_graph=True),
            ui.Range("Bad", 30, 80, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Lost", 80, 100, ui.Colour.red, show_on_graph=True),
        ],
    )

    # Ignition status
    ignition = ui.BooleanVariable("Ignition On", value=G62Tags.ignition)

    # Runtime
    runtime_s = ui.NumericVariable(
        "Runtime", value=G62Tags.runtime_s, units="s", precision=0
    )

    # Odometer
    odometer_km = ui.NumericVariable(
        "Odometer", value=G62Tags.odometer_km, units="km", precision=1
    )

    # External (system) voltage
    external_v = ui.NumericVariable(
        "System Voltage",
        value=G62Tags.external_v,
        units="V",
        precision=1,
        ranges=[
            ui.Range("Low", 9, 11.5, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Normal", 11.5, 13.0, ui.Colour.blue, show_on_graph=True),
            ui.Range("Charging", 13.0, 14.2, ui.Colour.green, show_on_graph=True),
            ui.Range("Over Voltage", 14.2, 15.0, ui.Colour.yellow, show_on_graph=True),
        ],
    )

    # Tracker battery
    battery_v = ui.NumericVariable(
        "Tracker Battery",
        value=G62Tags.battery_v,
        units="V",
        precision=2,
        ranges=[
            ui.Range("Low", 0, 3.4, ui.Colour.red, show_on_graph=True),
            ui.Range("OK", 3.4, 4.0, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Good", 4.0, 5.0, ui.Colour.green, show_on_graph=True),
        ],
    )

    # Device temperature
    temperature_c = ui.NumericVariable(
        "Device Temperature",
        value=G62Tags.temperature_c,
        units="\u00b0C",
        precision=0,
        ranges=[
            ui.Range("Cold", -20, 0, ui.Colour.blue, show_on_graph=True),
            ui.Range("Normal", 0, 35, ui.Colour.green, show_on_graph=True),
            ui.Range("Warm", 35, 50, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Hot", 50, 70, ui.Colour.red, show_on_graph=True),
        ],
    )

    # Heading
    heading_deg = ui.NumericVariable(
        "Heading", value=G62Tags.heading_deg, units="\u00b0", precision=0
    )

    # Analog / digital IO
    analog_input_v = ui.NumericVariable(
        "Analog Input", value=G62Tags.analog_input_v, units="V", precision=3
    )
    digital_input_1 = ui.BooleanVariable(
        "Digital Input 1", value=G62Tags.digital_input_1
    )
    digital_input_2 = ui.BooleanVariable(
        "Digital Input 2", value=G62Tags.digital_input_2
    )
    digital_output = ui.BooleanVariable("Digital Output", value=G62Tags.digital_output)

    # Status flags
    ext_power_good = ui.BooleanVariable("External Power", value=G62Tags.ext_power_good)
    gps_current = ui.BooleanVariable("GPS Fix Current", value=G62Tags.gps_current)

    # Last trip type (analogous to uplink reason)
    trip_type = ui.TextVariable("Trip Type", value=G62Tags.trip_type)


def export():
    G62UI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "g62_processor",
    )
