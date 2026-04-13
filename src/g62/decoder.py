"""Digital Matter G62 LoRaWAN payload decoder.

Spec: G62 LoRaWAN Integration revision 1.3 (Digital Matter, 2022).
All multi-byte fields are little-endian unless noted.
"""
from __future__ import annotations

TRIP_TYPES = {0: "None", 1: "Ignition", 2: "Movement", 3: "Run Detect"}


def _u16(b: bytes, o: int) -> int:
    return b[o] | (b[o + 1] << 8)


def _i8(b: bytes, o: int) -> int:
    v = b[o]
    return v - 0x100 if v & 0x80 else v


def _u32(b: bytes, o: int) -> int:
    return b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)


def _i28_latlon(b: bytes, o: int) -> float:
    """28-bit signed lat/lon. Low nibble of byte o is reserved (flags)."""
    raw = (b[o] & 0xF0) | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)
    if raw & 0x80000000:
        raw -= 0x100000000
    return raw / 1e7


def decode(payload: bytes, port: int) -> dict | None:
    if port == 1 and len(payload) in (17, 19):
        return _decode_full(payload)
    if port == 2 and len(payload) == 11:
        return _decode_part1(payload)
    if port == 3 and len(payload) in (6, 8):
        return _decode_part2(payload)
    if port == 4 and len(payload) == 8:
        return _decode_odometer(payload)
    if port == 5 and len(payload) == 3:
        return _decode_ack(payload)
    return None


def _decode_part1(b: bytes) -> dict:
    return {
        "_type": "data_part_1",
        "trip_type": TRIP_TYPES.get(b[0] & 0x03),
        "ext_power_good": bool(b[0] & 0x04),
        "gps_current": bool(b[0] & 0x08),
        "latitude": _i28_latlon(b, 0),
        "ignition": bool(b[4] & 0x01),
        "digital_input_1": bool(b[4] & 0x02),
        "digital_input_2": bool(b[4] & 0x04),
        "digital_output": bool(b[4] & 0x08),
        "longitude": _i28_latlon(b, 4),
        "heading_deg": b[8] * 2,
        "speed_kmh": b[9],
        "battery_v": b[10] * 0.02,
    }


def _decode_part2(b: bytes) -> dict:
    out = {
        "_type": "data_part_2",
        "external_v": _u16(b, 0) / 1000,
        "analog_input_v": _u16(b, 2) / 1000,
        "temperature_c": _i8(b, 4),
        "gps_accuracy_m": b[5],
    }
    if len(b) == 8:
        out["timestamp_mod"] = _u16(b, 6)
    return out


def _decode_full(b: bytes) -> dict:
    out = _decode_part1(b)
    out.update({
        "_type": "full_data",
        "external_v": _u16(b, 11) / 1000,
        "analog_input_v": _u16(b, 13) / 1000,
        "temperature_c": _i8(b, 15),
        "gps_accuracy_m": b[16],
    })
    if len(b) == 19:
        out["timestamp_mod"] = _u16(b, 17)
    return out


def _decode_odometer(b: bytes) -> dict:
    return {
        "_type": "odometer",
        "runtime_s": _u32(b, 0),
        "odometer_km": _u32(b, 4) * 0.01,
    }


def _decode_ack(b: bytes) -> dict:
    return {
        "_type": "downlink_ack",
        "sequence": b[0] & 0x7F,
        "accepted": bool(b[0] & 0x80),
        "firmware_version": f"{b[1]}.{b[2]}",
    }
