from pathlib import Path

from pydoover import ui

from .app_tags import G62Tags


class G62UI(ui.UI, hidden="$config.app().hide_ui"):
    trip_type = ui.TextVariable("Trip Type", value=G62Tags.trip_type)
    ignition = ui.BooleanVariable("Ignition", value=G62Tags.ignition)
    ext_power_good = ui.BooleanVariable("External Power", value=G62Tags.ext_power_good)
    gps_current = ui.BooleanVariable("GPS Fix Current", value=G62Tags.gps_current)

    speed_kmh = ui.NumericVariable(
        "Speed", value=G62Tags.speed_kmh, units="km/h", precision=0
    )
    heading_deg = ui.NumericVariable(
        "Heading", value=G62Tags.heading_deg, units="°", precision=0
    )
    gps_accuracy_m = ui.NumericVariable(
        "GPS Accuracy", value=G62Tags.gps_accuracy_m, units="m", precision=0
    )

    battery_v = ui.NumericVariable(
        "Battery",
        value=G62Tags.battery_v,
        units="V",
        precision=2,
        ranges=[
            ui.Range("Low", 0, 3.4, ui.Colour.red, show_on_graph=True),
            ui.Range("OK", 3.4, 4.0, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Good", 4.0, 5.0, ui.Colour.green, show_on_graph=True),
        ],
    )
    external_v = ui.NumericVariable(
        "External Voltage", value=G62Tags.external_v, units="V", precision=2
    )
    analog_input_v = ui.NumericVariable(
        "Analog Input", value=G62Tags.analog_input_v, units="V", precision=3
    )
    temperature_c = ui.NumericVariable(
        "Temperature", value=G62Tags.temperature_c, units="°C", precision=0
    )

    digital_input_1 = ui.BooleanVariable(
        "Digital Input 1", value=G62Tags.digital_input_1
    )
    digital_input_2 = ui.BooleanVariable(
        "Digital Input 2", value=G62Tags.digital_input_2
    )
    digital_output = ui.BooleanVariable("Digital Output", value=G62Tags.digital_output)

    runtime_s = ui.NumericVariable(
        "Runtime", value=G62Tags.runtime_s, units="s", precision=0
    )
    odometer_km = ui.NumericVariable(
        "Odometer", value=G62Tags.odometer_km, units="km", precision=2
    )


def export():
    G62UI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "g62_processor",
    )
