import base64
import json
import logging

from pydoover.cloud.processor import (
    Application,
    IngestionEndpointEvent,
)

from .app_config import DigitalMatterIntegrationConfig


log = logging.getLogger(__name__)


# Digital Matter uplink reason codes
UPLINK_REASONS = {
    0: "Reserved",
    1: "Start of trip",
    2: "End of trip",
    3: "Elapsed time",
    4: "Speed change",
    5: "Heading change",
    6: "Distance travelled",
    7: "Maximum Speed",
    8: "Stationary",
    9: "Ignition Changed",
    10: "Output Changed",
    11: "Heartbeat",
    12: "Harsh Brake",
    13: "Harsh Acceleration",
    14: "Harsh Cornering",
    15: "External Power Change",
    16: "System Power Monitoring",
    17: "Driver ID Tag Read",
    18: "Over speed",
    19: "Fuel sensor record",
    20: "Towing Alert",
    21: "Debug",
    22: "SDI-12 sensor data",
    23: "Accident",
    24: "Accident Data",
    25: "Sensor value elapsed time",
    26: "Sensor value change",
    27: "Sensor alarm",
    28: "Rain Gauge Tipped",
    29: "Tamper Alert",
    30: "BLOB notification",
    31: "Time and Attendance",
    32: "Trip Restart",
    33: "Tag Gained",
    34: "Tag Update",
    35: "Tag Lost",
    36: "Recovery Mode On",
    37: "Recovery Mode Off",
    38: "Immobiliser On",
    39: "Immobiliser Off",
    40: "Garmin FMI Stop Response",
    41: "Lone Worker Alarm",
    42: "Device Counters",
    43: "Connected Device Data",
    44: "Entered Geo-Fence",
    45: "Exited Geo-Fence",
    46: "High-G Event",
    47: "Third party data record",
    48: "Duress",
    49: "Cell Tower Connection",
    50: "Bluetooth Tag Data",
}


def get_uplink_reason(code: int) -> str:
    """Translate uplink reason code to human readable string."""
    return UPLINK_REASONS.get(code, f"Unknown ({code})")


def parse_dm_record(record: dict) -> dict:
    """
    Parse a single Digital Matter record into a normalized format.

    Digital Matter sends records with various field types (FType):
    - FType 0: GPS position data
    - FType 2: Digital inputs
    - FType 6: Analogue data (voltages, temperature, signal strength)
    - FType 27: Odometer and run hours
    """
    result = {
        "uplink_reason": get_uplink_reason(record.get("Reason", 0)),
        "uplink_reason_code": record.get("Reason"),
        "device_time_utc": record.get("DateUTC"),
        "sequence_number": record.get("SeqNo"),
    }

    fields = record.get("Fields", [])

    for field in fields:
        ftype = field.get("FType")

        if ftype == 0:
            # GPS position data
            lat = field.get("Lat", 0)
            lon = field.get("Long", 0)

            if lat != 0 and lon != 0:
                result["position"] = {
                    "lat": lat,
                    "long": lon,
                    "alt": field.get("Alt", 0),
                }
                # Speed is in cm/s, convert to km/h
                speed_cms = field.get("Spd", 0)
                result["speed_kmh"] = speed_cms * 0.036  # cm/s to km/h
                result["heading"] = field.get("Head", 0)
                result["gps_accuracy_m"] = field.get("PosAcc", 99)
                result["pdop"] = field.get("PDOP")
            else:
                result["gps_accuracy_m"] = 99

        elif ftype == 2:
            # Digital inputs
            din = field.get("DIn", 0)
            result["ignition_on"] = bool(din & 0b001)
            result["digital_input_2"] = bool(din & 0b010)
            result["digital_input_3"] = bool(din & 0b100)

        elif ftype == 6:
            # Analogue data
            analogue = field.get("AnalogueData", {})
            # Field 1: Internal battery voltage (mV)
            if "1" in analogue:
                result["battery_voltage"] = analogue["1"] / 1000
            # Field 2: External/system voltage (cV - centivolt)
            if "2" in analogue:
                result["system_voltage"] = analogue["2"] / 100
            # Field 3: Device temperature (cC - centi-celsius)
            if "3" in analogue:
                result["device_temp_c"] = analogue["3"] / 100
            # Field 4: Signal strength (0-31 scale)
            if "4" in analogue:
                result["signal_strength_percent"] = round(analogue["4"] * (100 / 31))

        elif ftype == 27:
            # Odometer and run hours
            # Odometer in cm, convert to km
            if "Odo" in field:
                result["odometer_km"] = field["Odo"] / 100000
            # Run hours in seconds, convert to hours
            if "RH" in field:
                result["run_hours"] = field["RH"] / 3600

        elif ftype == 9:
            # Trip data
            result["trip_distance_m"] = field.get("Dist")
            result["trip_idle_time_s"] = field.get("IdleTime")

    return result


class DigitalMatterIntegration(Application):
    config: DigitalMatterIntegrationConfig

    async def setup(self):
        log.info("Digital Matter integration initialized")

    def parse_ingestion_event_payload(self, payload: str) -> dict | None:
        """
        Parse the incoming payload from Digital Matter OEM Server.

        The OEM Server sends JSON payloads via HTTP POST containing device
        serial number and one or more records with telemetry data.
        """
        try:
            raw = base64.b64decode(payload)
            data = json.loads(raw)
            log.info(f"Parsed Digital Matter payload: {data}")
            return data
        except Exception as e:
            log.error(f"Failed to parse payload: {e}", exc_info=True)
            return None

    async def on_ingestion_endpoint(self, event: IngestionEndpointEvent):
        """
        Handle incoming data from Digital Matter OEM Server.

        The payload contains device serial number and telemetry records.
        We parse the data and forward it to the appropriate device agent.
        """
        payload = event.payload
        if payload is None:
            log.warning("Received empty payload")
            return

        log.info(f"Received Digital Matter event: {payload}")

        # Extract serial number - this identifies the device
        serial_number = payload.get("SerNo")
        if not serial_number:
            log.warning("No serial number in payload")
            return

        # Look up the agent ID for this serial number
        try:
            device_mapping = self._tag_values["digital_matter_processor-1"]["serial_number_lookup"]
        except KeyError:
            log.info(f"Serial numbers not found. Tags: {self._tag_values}. Skipping...")
            return

        agent_id = device_mapping.get(str(serial_number))

        log.info(f"Serial: {serial_number}, Agent ID: {agent_id}, Mapping: {device_mapping}")

        # Parse and process each record
        records = payload.get("Records", [])
        for record in records:
            parsed = parse_dm_record(record)
            parsed["serial_number"] = serial_number

            # Store the raw event on this integration's agent
            await self.api.publish_message(
                self.agent_id,
                "dm_events",
                parsed
            )

            # Forward to the device agent if we have a mapping
            if agent_id:
                log.info(f"Forwarding to agent {agent_id}: {parsed}")
                await self.api.publish_message(
                    agent_id,
                    "on_dm_event",
                    parsed
                )
