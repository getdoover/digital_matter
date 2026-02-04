from pydoover import ui


class DigitalMatterUI:
    def __init__(self):
        # Speed gauge
        self.speed = ui.NumericVariable(
            "speed",
            "Speed (km/h)",
            precision=1,
            ranges=[
                ui.Range("Low", 0, 20, ui.Colour.blue, show_on_graph=True),
                ui.Range("Normal", 20, 80, ui.Colour.green, show_on_graph=True),
                ui.Range("Fast", 80, 120, ui.Colour.yellow, show_on_graph=True),
            ],
        )

        # GPS accuracy
        self.gps_accuracy = ui.NumericVariable(
            "gps_accuracy",
            "GPS Accuracy (m)",
            precision=0,
            ranges=[
                ui.Range("Good", 0, 15, ui.Colour.green, show_on_graph=True),
                ui.Range("OK", 15, 30, ui.Colour.blue, show_on_graph=True),
                ui.Range("Bad", 30, 80, ui.Colour.yellow, show_on_graph=True),
                ui.Range("Lost", 80, 100, ui.Colour.red, show_on_graph=True),
            ],
        )

        # Ignition status
        self.ignition_on = ui.BooleanVariable(
            "ignition_on",
            "Ignition On",
        )

        # Run hours
        self.run_hours = ui.NumericVariable(
            "run_hours",
            "Machine Hours (hrs)",
            precision=2,
        )

        # Odometer
        self.odometer = ui.NumericVariable(
            "odometer",
            "Odometer (km)",
            precision=1,
        )

        # System voltage
        self.system_voltage = ui.NumericVariable(
            "system_voltage",
            "System Voltage (V)",
            precision=1,
            ranges=[
                ui.Range("Low", 9, 11.5, ui.Colour.yellow, show_on_graph=True),
                ui.Range("Normal", 11.5, 13.0, ui.Colour.blue, show_on_graph=True),
                ui.Range("Charging", 13.0, 14.2, ui.Colour.green, show_on_graph=True),
                ui.Range("Over Voltage", 14.2, 15.0, ui.Colour.yellow, show_on_graph=True),
            ],
        )

        # Battery voltage (internal tracker battery)
        self.battery_voltage = ui.NumericVariable(
            "battery_voltage",
            "Tracker Battery (V)",
            precision=2,
            ranges=[
                ui.Range("Low", 3.0, 3.5, ui.Colour.yellow, show_on_graph=True),
                ui.Range("Normal", 3.5, 3.8, ui.Colour.blue, show_on_graph=True),
                ui.Range("Good", 3.8, 4.2, ui.Colour.green, show_on_graph=True),
                ui.Range("Over Voltage", 4.2, 4.5, ui.Colour.yellow, show_on_graph=True),
            ],
        )

        # Signal strength
        self.signal_strength = ui.NumericVariable(
            "signal_strength",
            "Cellular Signal (%)",
            precision=0,
            ranges=[
                ui.Range("Low", 0, 30, ui.Colour.yellow, show_on_graph=True),
                ui.Range("OK", 30, 60, ui.Colour.blue, show_on_graph=True),
                ui.Range("Strong", 60, 100, ui.Colour.green, show_on_graph=True),
            ],
        )

        # Device temperature
        self.device_temp = ui.NumericVariable(
            "device_temp",
            "Device Temperature (°C)",
            precision=0,
            ranges=[
                ui.Range("Cold", -20, 0, ui.Colour.blue, show_on_graph=True),
                ui.Range("Normal", 0, 35, ui.Colour.green, show_on_graph=True),
                ui.Range("Warm", 35, 50, ui.Colour.yellow, show_on_graph=True),
                ui.Range("Hot", 50, 70, ui.Colour.red, show_on_graph=True),
            ],
        )

        # Last uplink reason
        self.uplink_reason = ui.TextVariable(
            "uplink_reason",
            "Last Uplink Reason",
        )

        # Device time
        self.device_time = ui.DateTimeVariable(
            "device_time",
            "Device Time (UTC)",
        )

    def fetch(self):
        """Return UI elements for the UI manager."""
        return (
            self.speed,
            self.gps_accuracy,
            self.ignition_on,
            self.run_hours,
            self.odometer,
            self.system_voltage,
            self.battery_voltage,
            self.signal_strength,
            self.device_temp,
            self.uplink_reason,
            self.device_time,
        )

    def update(self, data: dict, odometer_offset: float = 0.0, run_hours_offset: float = 0.0):
        """Update UI from parsed Digital Matter event data."""
        # Speed
        if "speed_kmh" in data:
            self.speed.update(data["speed_kmh"])

        # GPS accuracy
        if "gps_accuracy_m" in data:
            self.gps_accuracy.update(data["gps_accuracy_m"])

        # Ignition
        if "ignition_on" in data:
            self.ignition_on.update(data["ignition_on"])

        # Run hours with offset
        if "run_hours" in data:
            self.run_hours.update(data["run_hours"] + run_hours_offset)

        # Odometer with offset
        if "odometer_km" in data:
            self.odometer.update(data["odometer_km"] + odometer_offset)

        # System voltage
        if "system_voltage" in data:
            self.system_voltage.update(data["system_voltage"])

        # Battery voltage
        if "battery_voltage" in data:
            self.battery_voltage.update(data["battery_voltage"])

        # Signal strength
        if "signal_strength_percent" in data:
            self.signal_strength.update(data["signal_strength_percent"])

        # Device temperature
        if "device_temp_c" in data:
            self.device_temp.update(data["device_temp_c"])

        # Uplink reason
        if "uplink_reason" in data:
            self.uplink_reason.update(data["uplink_reason"])

        # Device time
        if "device_time_utc" in data:
            self.device_time.update(data["device_time_utc"])

    def get_status_display(self, data: dict) -> tuple[str, str | None]:
        """
        Get status display string and icon based on device state.

        Returns:
            Tuple of (display_string, status_icon)
        """
        ignition_on = data.get("ignition_on")
        speed = data.get("speed_kmh", 0)

        if ignition_on is None:
            return "Unknown", None

        if not ignition_on:
            return "Off", "off"
        elif speed is None or speed <= 1:
            return "Idle", "idle"
        else:
            return "Running", None
