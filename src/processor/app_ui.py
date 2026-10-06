from pathlib import Path

from pydoover import ui

from .app_tags import DigitalMatterTags, analogue_tag_name, digital_tag_name

# Elements that only make sense on a vehicle tracker.
VEHICLE_ELEMENTS = ("speed", "gps_accuracy", "ignition_on", "run_hours", "odometer", "analog_input")

# Elements for temporarily powering a Hawk's sensors and speeding up its updates.
POWER_ON_ELEMENTS = ("power_on", "power_on_status", "power_on_until")

# Digital inputs sit at 60 + their number, so this keeps Power On below them.
POWER_ON_POSITION = 100


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

    # External analog input (G70 yellow wire, mapped to "Analog 5" on the device)
    analog_input = ui.NumericVariable(
        "Analog Input",
        value=DigitalMatterTags.analog_input_v,
        units="V",
        precision=3,
    )

    # Last uplink reason
    uplink_reason = ui.TextVariable(
        "Last Uplink Reason",
        value=DigitalMatterTags.uplink_reason,
    )

    power_on = ui.Button(
        "Power On for 30 min", name="power_on", position=POWER_ON_POSITION
    )

    power_on_status = ui.TextVariable(
        "Power On Status",
        value=DigitalMatterTags.power_on_status,
        hidden=DigitalMatterTags.power_on_hidden,
        position=POWER_ON_POSITION + 1,
    )

    power_on_until = ui.Timestamp(
        "Power On Until",
        value=DigitalMatterTags.power_on_until,
        hidden=DigitalMatterTags.power_on_hidden,
        position=POWER_ON_POSITION + 2,
    )

    async def setup(self):
        if self.config is None:
            return

        # Power On changes the Hawk's config, so needs it managed from here.
        if self.config.is_vehicle_tracker or not self.config.manage_device_config.value:
            for name in POWER_ON_ELEMENTS:
                self.remove_element(name)

        if self.config.is_vehicle_tracker:
            return

        for name in VEHICLE_ELEMENTS:
            self.remove_element(name)

        self.add_input_elements(self.tags.detected_inputs.value or {})

    def add_input_elements(self, detected: dict):
        """Add a raw-value element for each detected input not already shown.

        Positioned ahead of the health readings, analogue slots first.
        """
        for number in detected.get("analogue", []):
            name = analogue_tag_name(number)
            if name not in self._elements:
                self.add_element(
                    ui.NumericVariable(
                        f"Analogue {number}",
                        name=name,
                        value=self.tags.get_tag(name),
                        precision=0,
                        position=number,
                    )
                )
        for number in detected.get("digital", []):
            name = digital_tag_name(number)
            if name not in self._elements:
                self.add_element(
                    ui.BooleanVariable(
                        f"Digital Input {number}",
                        name=name,
                        value=self.tags.get_tag(name),
                        position=60 + number,
                    )
                )


def export():
    DigitalMatterUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json",
        "digital_matter_processor"
    )
