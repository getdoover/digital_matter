# Digital Matter Connector

Doover integration for [Digital Matter](https://www.digitalmatter.com/) GPS tracking devices.

This integration receives data from Digital Matter's OEM Server (Device Manager) via HTTP webhooks and displays device telemetry in the Doover platform.


### 1. Digital Matter Integration (`INT`)

Receives HTTP POST requests from Digital Matter OEM Server containing device telemetry data in JSON format. The integration:

- Parses incoming payloads with device serial number and telemetry records
- Extracts GPS position, speed, voltages, odometer, run hours, and other data
- Looks up the Doover agent ID for each device by serial number
- Forwards parsed data to device-specific channels

### 2. Digital Matter Processor (`PRO`)

Installed on individual device agents, this processor:

- Subscribes to the `on_dm_event` channel
- Updates the device UI with telemetry data
- Publishes location updates to the `location` channel
- Manages device connection status

## Supported Data

The integration parses the following Digital Matter field types:

| Field Type | Data |
|------------|------|
| FType 0 | GPS position (lat, long, altitude, speed, accuracy) |
| FType 2 | Digital inputs (ignition state) |
| FType 6 | Analogue data (battery voltage, system voltage, temperature, signal strength) |
| FType 9 | Trip data (distance, idle time) |
| FType 27 | Odometer and run hours |

## Setup

### 1. Install the Integration

Install the Digital Matter Integration on your organization in Doover. Configure:

- **CIDR Ranges**: IP addresses allowed to send data (get from Digital Matter)
- **Extended Permissions**: Grant access to devices that will receive data

### 2. Configure OEM Server

In Digital Matter's Device Manager (OEM Server):

1. Create an HTTP/HTTPS connector
2. Set the endpoint URL to your Doover ingestion endpoint
3. Configure authentication if required

### 3. Register Devices

For each Digital Matter device:

1. Create a device agent in Doover
2. Install the Digital Matter Processor
3. Configure the processor to subscribe to `on_dm_event`
4. Add the device serial number to the `dm_devices` tag on the integration

The `dm_devices` tag should be a JSON object mapping serial numbers to agent IDs:

```json
{
  "123456": "agent-id-for-device-123456",
  "789012": "agent-id-for-device-789012"
}
```

## Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Install Dependencies

```bash
uv sync
```

### Export Config Schemas

```bash
uv run export-config-integration
uv run export-config-processor
```

### Build Package

```bash
./build.sh
```

### Publish

```bash
doover app publish --profile dv2
```

## References

- [Digital Matter Support](https://support.digitalmatter.com/)
- [Digital Matter HTTP/HTTPS Connector](https://support.digitalmatter.com/en_US/the-httphttps-connector)
- [Doover Documentation](https://docs.doover.com/)
