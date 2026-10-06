"""Minimal client for the Digital Matter Device Manager REST API.

Docs: https://api.oemserver.com/swagger/index.html
"""

import base64
import json
import re

import aiohttp

API_URL = "https://api.oemserver.com/v1"

# Products whose current parameters the API can read, by ProductId. Anything
# else (notably the Hawk, 142) has no read endpoint.
READABLE_PRODUCTS = {88: "Bolt2", 89: "G704G", 97: "Yabby34G"}


class DeviceManagerError(Exception):
    pass


def normalise_serial(serial: str | int) -> str:
    """DM serials are numbers; the API 404s on the leading zeros labels show."""
    return str(int(serial))


class DeviceManagerClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(self, method: str, path: str, raw: bool = False, **kwargs):
        async with self.session.request(
            method, f"{API_URL}/{path}", headers=self.headers, **kwargs
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise DeviceManagerError(f"{method} {path} failed ({resp.status}): {body[:200]}")
            if raw:
                return body
            return json.loads(body) if body else None

    async def lookup_product(self, serial: str) -> int:
        """The ProductId of the device with this serial."""
        serial = normalise_serial(serial)
        result = await self._request(
            "POST", "TrackingDevice/LookupSerialProduct", json={"SerialNumber": serial}
        )
        # "Products" is base64 bytes, one ProductId per byte.
        products = list(base64.b64decode(result.get("Products") or ""))
        if len(products) == 1:
            return products[0]

        # The lookup isn't scoped to our account, so a serial shared across
        # products is resolved against the devices we actually own.
        devices = await self._request("GET", "TrackingDevice/GetDeviceList")
        owned = [
            d["ProductId"] for d in devices["Devices"]
            if normalise_serial(d["SerialNumber"]) == serial
        ]
        if len(owned) != 1:
            raise DeviceManagerError(f"Couldn't find the product for serial {serial} (got {owned or products}).")
        return owned[0]

    async def get_defaults(self, product_id: int) -> dict[int, dict[str, str]]:
        """Every parameter section this product has, with DM's default values."""
        text = await self._request(
            "GET", "TrackingDevice/GetProductDefaultDeviceParameters", params={"id": product_id}, raw=True
        )
        # It's JSON annotated with // comments describing each param.
        defaults = json.loads(re.sub(r"//[^\n]*", "", text))
        return {s["Id"]: s["Params"] for s in defaults["ParamSections"]}

    async def get_parameters(self, product_id: int, serial: str) -> dict[int, dict[str, str]] | None:
        """The device's current parameters, or None if they can't be read.

        DM only returns the sections that have been set; the rest are at the
        product defaults.
        """
        controller = READABLE_PRODUCTS.get(product_id)
        if controller is None:
            return None
        device = await self._request("GET", f"{controller}/Get", params={"id": normalise_serial(serial)})
        return {int(k): v for k, v in (device.get("SystemParameters") or {}).items()}

    async def set_parameters(self, product_id: int, serial: str, sections: dict[int, dict[str, str]]):
        """Queue parameter changes; the device picks them up on its next check-in.

        Only the params given are changed. ``id`` must be the ProductId; without
        it DM accepts the request but returns false and changes nothing.
        """
        ok = await self._request(
            "PUT",
            "TrackingDevice/SetDeviceParameters",
            params={"id": product_id},
            json={
                "Devices": [int(normalise_serial(serial))],
                "ParamSections": [{"Id": k, "Params": v} for k, v in sections.items()],
            },
        )
        if ok is not True:
            raise DeviceManagerError(f"Device Manager rejected the parameters for serial {serial}.")
