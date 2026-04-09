from pathlib import Path

from pydoover import ui

from .app_tags import DigitalMatterTags


class DigitalMatterUI(ui.UI, hidden="$config.app().hide_ui"):
    # Speed gauge
    speed = ui.NumericVariable(
        "Speed",
        value=DigitalMatterTags.speed,
        units="km/h",
        precision=1,
        ranges=[
            ui.Range("Low", 0, 20, ui.Colour.blue, show_on_graph=True),
            ui.Range("Normal", 20, 80, ui.Colour.green, show_on_graph=True),
            ui.Range("Fast", 80, 120, ui.Colour.yellow, show_on_graph=True),
        ],
    )

    # GPS accuracy
    gps_accuracy = ui.NumericVariable(
        "GPS Accuracy",
        value=DigitalMatterTags.gps_accuracy,
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
    ignition_on = ui.BooleanVariable(
        "Ignition On",
        value=DigitalMatterTags.ignition_on,
    )

    # Run hours
    run_hours = ui.NumericVariable(
        "Machine Hours",
        value=DigitalMatterTags.run_hours,
        units="hrs",
        precision=2,
    )

    # Odometer
    odometer = ui.NumericVariable(
        "Odometer",
        value=DigitalMatterTags.odometer_km,
        units="km",
        precision=1,
    )

    # System voltage
    system_voltage = ui.NumericVariable(
        "System Voltage",
        value=DigitalMatterTags.system_voltage,
        units="V",
        precision=1,
        ranges=[
            ui.Range("Low", 9, 11.5, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Normal", 11.5, 13.0, ui.Colour.blue, show_on_graph=True),
            ui.Range("Charging", 13.0, 14.2, ui.Colour.green, show_on_graph=True),
            ui.Range("Over Voltage", 14.2, 15.0, ui.Colour.yellow, show_on_graph=True),
        ],
    )

    # Battery voltage (internal tracker battery)
    battery_voltage = ui.NumericVariable(
        "Tracker Battery",
        value=DigitalMatterTags.battery_voltage,
        units="V",
        precision=2,
        ranges=[
            ui.Range("Low", 3.0, 3.5, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Normal", 3.5, 3.8, ui.Colour.blue, show_on_graph=True),
            ui.Range("Good", 3.8, 4.2, ui.Colour.green, show_on_graph=True),
            ui.Range("Over Voltage", 4.2, 4.5, ui.Colour.yellow, show_on_graph=True),
        ],
    )

    # Signal strength
    signal_strength = ui.NumericVariable(
        "Cellular Signal",
        value=DigitalMatterTags.signal_strength,
        units="%",
        precision=0,
        ranges=[
            ui.Range("Low", 0, 30, ui.Colour.yellow, show_on_graph=True),
            ui.Range("OK", 30, 60, ui.Colour.blue, show_on_graph=True),
            ui.Range("Strong", 60, 100, ui.Colour.green, show_on_graph=True),
        ],
    )

    # Device temperature
    device_temp = ui.NumericVariable(
        "Device Temperature",
        value=DigitalMatterTags.device_temp,
        units="\u00b0C",
        precision=0,
        ranges=[
            ui.Range("Cold", -20, 0, ui.Colour.blue, show_on_graph=True),
            ui.Range("Normal", 0, 35, ui.Colour.green, show_on_graph=True),
            ui.Range("Warm", 35, 50, ui.Colour.yellow, show_on_graph=True),
            ui.Range("Hot", 50, 70, ui.Colour.red, show_on_graph=True),
        ],
    )

    # Last uplink reason
    uplink_reason = ui.TextVariable(
        "Last Uplink Reason",
        value=DigitalMatterTags.uplink_reason,
    )

    # Device time
    device_time = ui.DateTimeVariable(
        "Device Time (UTC)",
        value=DigitalMatterTags.device_time,
    )


def export():
    DigitalMatterUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )
