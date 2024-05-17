import logging

from pydoover.cloud import ProcessorBase, Channel


class target(ProcessorBase):
    oem_uplink_channel: Channel
    ui_state_channel: Channel
    ui_cmds_channel: Channel
    location_channel: Channel

    def setup(self):
        # Get the required channels
        self.oem_uplink_channel = self.fetch_channel_named("dm_oem_uplink_recv")
        self.ui_state_channel = self.api.get_channel_named("ui_state", self.agent_id)
        self.ui_cmds_channel = self.api.get_channel_named("ui_cmds", self.agent_id)
        self.location_channel = self.api.get_channel_named("location", self.agent_id)

    def process(self):
        message_type = self.package_config.get("message_type")

        if message_type == "DEPLOY":
            self.on_deploy()
        elif message_type == "DOWNLINK":
            self.on_downlink()
        elif message_type == "UPLINK":
            self.on_uplink()

    def on_deploy(self):
        ## Run any deployment code here

        ui_obj = {
            "state": {
                "type": "uiContainer",
                "displayString": "",
                "children": {
                    "location": {
                        "type": "uiVariable",
                        "varType": "location",
                        "hide": True,
                        "name": "location",
                        "displayString": "Location",
                    },
                    "speed": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "speed",
                        "displayString": "Speed (km/h)",
                        "decPrecision": 1,
                        "form": "radialGauge",
                        "ranges": [
                            {
                                "label": "Low",
                                "min": 0,
                                "max": 20,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                # "label" : "Ok",
                                "min": 20,
                                "max": 80,
                                "colour": "green",
                                "showOnGraph": True
                            },
                            {
                                "label": "Fast",
                                "min": 80,
                                "max": 120,
                                "colour": "yellow",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "gpsAccuracy": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "gpsAccuracy",
                        "displayString": "GPS accuracy (m)",
                        "decPrecision": 0,
                        "ranges": [
                            {
                                "label": "Good",
                                "min": 0,
                                "max": 15,
                                "colour": "green",
                                "showOnGraph": True
                            },
                            {
                                "label": "Ok",
                                "min": 15,
                                "max": 30,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                "label": "Bad",
                                "min": 30,
                                "max": 80,
                                "colour": "yellow",
                                "showOnGraph": True
                            },
                            {
                                "label": "Lost",
                                "min": 80,
                                "max": 100,
                                "colour": "red",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "ignitionOn": {
                        "type": "uiVariable",
                        "varType": "bool",
                        "name": "ignitionOn",
                        "displayString": "Ignition On",
                    },
                    "deviceRunHours": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "deviceRunHours",
                        "displayString": "Machine Hours (hrs)",
                        "decPrecision": 2,
                    },
                    "deviceOdometer": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "deviceOdometer",
                        "displayString": "Machine Odometer (km)",
                        "decPrecision": 1,
                    },
                    "sysVoltage": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "sysVoltage",
                        "displayString": "System Voltage (V)",
                        "decPrecision": 1,
                        "ranges": [
                            {
                                "label": "Low",
                                "min": 9,
                                "max": 11.5,
                                "colour": "yellow",
                                "showOnGraph": True
                            },
                            {
                                # "label" : "Ok",
                                "min": 11.5,
                                "max": 13.0,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                "label": "Charging",
                                "min": 13.0,
                                "max": 14.2,
                                "colour": "green",
                                "showOnGraph": True
                            },
                            {
                                "label": "Over Voltage",
                                "min": 14.2,
                                "max": 15.0,
                                "colour": "yellow",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "battVoltage": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "battVoltage",
                        "displayString": "Tracker Battery (V)",
                        "decPrecision": 1,
                        "ranges": [
                            {
                                "label": "Low",
                                "min": 3.0,
                                "max": 3.5,
                                "colour": "yellow",
                                "showOnGraph": True
                            },
                            {
                                # "label" : "Ok",
                                "min": 3.5,
                                "max": 3.8,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                "label": "Good",
                                "min": 3.8,
                                "max": 4.2,
                                "colour": "green",
                                "showOnGraph": True
                            },
                            {
                                "label": "Over Voltage",
                                "min": 4.2,
                                "max": 4.5,
                                "colour": "yellow",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "dataSignalStrength": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "dataSignalStrength",
                        "displayString": "Cellular Signal (%)",
                        "decPrecision": 0,
                        "ranges": [
                            {
                                "label": "Low",
                                "min": 0,
                                "max": 30,
                                "colour": "yellow",
                                "showOnGraph": True
                            },
                            {
                                "label": "Ok",
                                "min": 30,
                                "max": 60,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                "label": "Strong",
                                "min": 60,
                                "max": 100,
                                "colour": "green",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "deviceTemp": {
                        "type": "uiVariable",
                        "varType": "float",
                        "name": "deviceTemp",
                        "displayString": "Device Temperature (C)",
                        "decPrecision": 0,
                        "ranges": [
                            {
                                "label": "Low",
                                "min": 0,
                                "max": 20,
                                "colour": "blue",
                                "showOnGraph": True
                            },
                            {
                                # "label" : "Ok",
                                "min": 20,
                                "max": 35,
                                "colour": "green",
                                "showOnGraph": True
                            },
                            {
                                "label": "Warm",
                                "min": 35,
                                "max": 50,
                                "colour": "yellow",
                                "showOnGraph": True
                            }
                        ]
                    },
                    "lastUplinkReason": {
                        "type": "uiVariable",
                        "varType": "text",
                        "name": "lastUplinkReason",
                        "displayString": "Reason for uplink",
                    },
                    "deviceTimeUtc": {
                        "type": "uiVariable",
                        "varType": "datetime",
                        "name": "deviceTimeUtc",
                        "displayString": "Device Time (UTC)",
                    },
                    "node_connection_info": {
                        "type": "uiConnectionInfo",
                        "name": "node_connection_info",
                        "connectionType": "periodic",
                        # "connectionPeriod": 1800,
                        # "nextConnection": 1800
                        "connectionPeriod": 600,
                        "nextConnection": 600,
                    }
                }
            }
        }

        self.ui_state_channel.publish(ui_obj)

        # Publish a dummy message to oem_uplink to trigger a new process of data
        self.oem_uplink_channel.publish({}, save_log=False, log_aggregate=False)

    def on_downlink(self):
        # Run any downlink processing code here
        pass

    def on_uplink(self):
        # Run any uplink processing code here
        if not (self.message and self.message.id):
            logging.info("No trigger message passed - skipping processing")
            return

        if 'Records' not in self.message.fetch_payload():
            logging.info("No records in payload - skipping processing")
            return

        for record in self.message.fetch_payload():
            fields = record.get("Fields")
            if not fields:
                logging.info("No fields in record - skipping processing")
                return

            device_uplink_reason = record['Reason']
            device_time_utc = record['DateUTC']

            position = None
            gps_accuracy_m = None
            speed_kmh = None
            ignition_on = None
            device_run_hours = None
            device_odometer = None
            sys_voltage = None
            batt_voltage = None
            device_temp = None
            data_signal_strength = None

            for f in fields:

                if 'FType' not in f:
                    continue

                if f['FType'] == 0:
                    gps_accuracy_m = 99
                    if f['Lat'] != 0 and f['Long'] != 0:
                        position = {
                            'lat': f['Lat'],
                            'long': f['Long'],
                            'alt': f['Alt'],
                        }
                        speed_kmh = f['Spd'] * (3.6 / 100)
                        gps_accuracy_m = f['PosAcc']

                if f['FType'] == 2:
                    ignition_on = (f['DIn'] & 0b001 != 0)

                if f['FType'] == 6:
                    batt_voltage = f['AnalogueData']['1'] / 1000
                    sys_voltage = f['AnalogueData']['2'] / 100
                    device_temp = f['AnalogueData']['3'] / 100
                    data_signal_strength = round(
                        f['AnalogueData']['4'] * (100 / 31))  # Signal quality between 0-31

                if f['FType'] == 27:
                    device_odometer = f['Odo'] / 100
                    device_run_hours = f['RH'] / (60 * 60)

                    odometer_offset = self.get_agent_config('ODO_OFFSET')
                    machine_hours_offset = self.get_agent_config('MACHINE_HOURS_OFFSET')

                    if odometer_offset is not None:
                        logging.info("Applying odometer offset of " + str(odometer_offset))
                        device_odometer = device_odometer + odometer_offset

                    if machine_hours_offset is not None:
                        logging.info("Applying machine hours offset of " + str(machine_hours_offset))
                        device_run_hours = device_run_hours + machine_hours_offset

            if position is not None:
                self.location_channel.publish(position, save_log=True)

            if ignition_on is not None:

                if not ignition_on:
                    status_icon = "off"
                    display_string = "Off"
                elif speed_kmh is None or speed_kmh <= 1:
                    status_icon = "idle"
                    display_string = "Idle"
                else:
                    status_icon = None
                    display_string = "Running"

                to_publish = {
                    "state": {
                        "displayString": display_string,
                        "statusIcon": status_icon,
                        "children": {
                            "location": {
                                "currentValue": position,
                            },
                            "speed": {
                                "currentValue": speed_kmh,
                            },
                            "gpsAccuracy": {
                                "currentValue": gps_accuracy_m,
                            },
                            "ignitionOn": {
                                "currentValue": ignition_on,
                            },
                            "deviceRunHours": {
                                "currentValue": device_run_hours,
                            },
                            "deviceOdometer": {
                                "currentValue": device_odometer,
                            },
                            "sysVoltage": {
                                "currentValue": sys_voltage,
                            },
                            "battVoltage": {
                                "currentValue": batt_voltage,
                            },
                            "dataSignalStrength": {
                                "currentValue": data_signal_strength,
                            },
                            "deviceTemp": {
                                "currentValue": device_temp,
                            },
                            "lastUplinkReason": {
                                "currentValue": self.uplink_reason_translate(device_uplink_reason),
                            },
                            "deviceTimeUtc": {
                                "currentValue": device_time_utc,
                            },
                        }
                    }
                }
                self.ui_state_channel.publish(to_publish, save_log=True)

    @staticmethod
    def uplink_reason_translate(reason_code):
        reasons = {
            0: 'Reserved',
            1: 'Start of trip',
            2: 'End of trip',
            3: 'Elapsed time',
            4: 'Speed change',
            5: 'Heading change',
            6: 'Distance travelled',
            7: 'Maximum Speed',
            8: 'Stationary',
            9: 'Ignition Changed',
            10: 'Output Changed',
            11: 'Heartbeat',
            12: 'Harsh Brake ',
            13: 'Harsh Acceleration',
            14: 'Harsh Cornering',
            15: 'External Power Change  ',
            16: 'System Power Monitoring',
            17: 'Driver ID Tag Read',
            18: 'Over speed',
            19: 'Fuel sensor record',
            20: 'Towing Alert',
            21: 'Debug',
            22: 'SDI-12 sensor data',
            23: 'Accident',
            24: 'Accident Data',
            25: 'Sensor value elapsed time',
            26: 'Sensor value change',
            27: 'Sensor alarm',
            28: 'Rain Gauge Tipped',
            29: 'Tamper Alert',
            30: 'BLOB notification',
            31: 'Time and Attendance',
            32: 'Trip Restart',
            33: 'Tag Gained',
            34: 'Tag Update',
            35: 'Tag Lost',
            36: 'Recovery Mode On',
            37: 'Recovery Mode Off',
            38: 'Immobiliser On',
            39: 'Immobiliser Off',
            40: 'Garmin FMI Stop Response ',
            41: 'Lone Worker Alarm',
            42: 'Device Counters',
            43: 'Connected Device Data',
            44: 'Entered Geo-Fence ',
            45: 'Exited Geo-Fence ',
            46: 'High-G Event',
            47: 'Third party data record',
            48: 'Duress',
            49: 'Cell Tower Connection',
            50: 'Bluetooth Tag Data',
        }

        if reason_code in reasons:
            return reasons[reason_code]
        else:
            return "Unknown reason"
