#!/usr/bin/python3
import os, sys, time, json, datetime, pytz, traceback
from dateutil.relativedelta import relativedelta

## This is the definition for a tiny lambda function
## Which is run in response to messages processed in Doover's 'Channels' system

## In the doover_config.json file we have defined some of these subscriptions
## These are under 'processor_deployments' > 'tasks'


## You can import the pydoover module to interact with Doover based on decisions made in this function
## Just add the current directory to the path first

## attempt to delete any loaded pydoover modules that persist across lambdas
if 'pydoover' in sys.modules:
    del sys.modules['pydoover']
try: del pydoover
except: pass
try: del pd
except: pass

# sys.path.append(os.path.dirname(__file__))
import pydoover as pd


class target:

    def __init__(self, *args, **kwargs):

        self.kwargs = kwargs
        ### kwarg
        #     'agent_id' : The Doover agent id invoking the task e.g. '9843b273-6580-4520-bdb0-0afb7bfec049'
        #     'access_token' : A temporary token that can be used to interact with the Doover API .e.g 'ABCDEFGHJKLMNOPQRSTUVWXYZ123456890',
        #     'api_endpoint' : The API endpoint to interact with e.g. "https://my.doover.com",
        #     'package_config' : A dictionary object with configuration for the task - as stored in the task channel in Doover,
        #     'msg_obj' : A dictionary object of the msg that has invoked this task,
        #     'task_id' : The identifier string of the task channel used to run this processor,
        #     'log_channel' : The identifier string of the channel to publish any logs to
        #     'agent_settings' : {
        #       'deployment_config' : {} # a dictionary of the deployment config for this agent
        #     }


    ## This function is invoked after the singleton instance is created
    def execute(self):

        start_time = time.time()

        self.create_doover_client()

        self.add_to_log( "kwargs = " + str(self.kwargs) )
        self.add_to_log( str( start_time ) )

        try:

            ## Get the oem_uplink channel
            self.oem_uplink_channel = self.cli.get_channel(
                channel_name="dm_oem_uplink_recv",
                agent_id=self.kwargs['agent_id']
            )

            ## Get the state channel
            self.ui_state_channel = self.cli.get_channel(
                channel_name="ui_state",
                agent_id=self.kwargs['agent_id']
            )

            ## Get the cmds channel
            self.ui_cmds_channel = self.cli.get_channel(
                channel_name="ui_cmds",
                agent_id=self.kwargs['agent_id']
            )

            ## Get the location channel
            self.location_channel = self.cli.get_channel(
                channel_name="location",
                agent_id=self.kwargs['agent_id']
            )

            ## Get the notifications channel
            self.notifications_channel = self.cli.get_channel(
                channel_name="significantEvent",
                agent_id=self.kwargs['agent_id']
            )

            ## Get the recent activity channel
            self.recent_activity_channel = self.cli.get_channel(
                channel_name="activity_logs",
                agent_id=self.kwargs['agent_id']
            )
            
            ## Do any processing you would like to do here
            message_type = None
            if 'message_type' in self.kwargs['package_config'] and 'message_type' is not None:
                message_type = self.kwargs['package_config']['message_type']

            if message_type == "DEPLOY":
                self.deploy()

            if message_type == "DOWNLINK":
                self.downlink()

            if message_type == "UPLINK":
                self.uplink()

        except Exception as e:
            self.add_to_log("ERROR attempting to process message - " + str(e))
            self.add_to_log(traceback.format_exc())

        self.complete_log()



    def deploy(self):
        ## Run any deployment code here

        ui_obj = {
            "state" : {
                "type" : "uiContainer",
                "displayString" : "",
                "children" : {
                    "deviceRunHours" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "deviceRunHours",
                        "displayString" : "Machine Hours (hrs)",
                        "decPrecision": 1,
                    },
                    "deviceOdometer" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "deviceOdometer",
                        "displayString" : "Odometer (km)",
                        "decPrecision": 1,
                    },
                    "nextServiceEst" : {
                        "type" : "uiVariable",
                        "varType" : "text",
                        "name" : "nextServiceEst",
                        "displayString" : "Next Service Estimate",
                    },
                    "daysTillNextService" : {
                        "type" : "uiVariable",
                        "varType" : "text",
                        "name" : "daysTillNextService",
                        "displayString" : "Days To Next Service",
                    },
                    "smsServiceAlert": {
                        "type": "uiAlertStream",
                        "name": "significantEvent",
                        "displayString": ("Text me " + str(self.get_sms_alert_days()) + " days before next service"),
                    },
                    "hoursTillNextService" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "hoursTillNextService",
                        "displayString" : "Hours To Next Service",
                    },
                    "kmsTillNextService" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "kmsTillNextService",
                        "displayString" : "Kms Till Next Service",
                    },
                    "aveHoursPerDay" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "aveHoursPerDay",
                        "displayString" : "Ave Hours Per Day",
                        "decPrecision": 1,
                    },
                    "aveKmsPerDay" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "aveKmsPerDay",
                        "displayString" : "Ave Kms Per Day",
                        "decPrecision": 1,
                    },
                    "ignitionOn" : {
                        "type" : "uiVariable",
                        "varType" : "bool",
                        "name" : "ignitionOn",
                        "displayString" : "Ignition On",
                    },
                    "location" : {
                        "type" : "uiVariable",
                        "varType" : "location",
                        "hide" : True,
                        "name" : "location",
                        "displayString" : "Location",
                    },
                    "speed" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "speed",
                        "displayString" : "Speed (km/h)",
                        "decPrecision": 1,
                        "form": "radialGauge",
                        "ranges": [
                            {
                                "label" : "Low",
                                "min" : 0,
                                "max" : 20,
                                "colour" : "blue",
                                "showOnGraph" : True
                            },
                            {
                                # "label" : "Ok",
                                "min" : 20,
                                "max" : 80,
                                "colour" : "green",
                                "showOnGraph" : True
                            },
                            {
                                "label" : "Fast",
                                "min" : 80,
                                "max" : 120,
                                "colour" : "yellow",
                                "showOnGraph" : True
                            }
                        ]
                    },
                    "maintenance_submodule": {
                        "type": "uiSubmodule",
                        "name": "maintenance_submodule",
                        "displayString": "Maintenance",
                        "children": {
                            "lastServiceDate" : {
                                "type" : "uiDatetimeParam",
                                "includeTime" : False,
                                "name" : "lastServiceDate",
                                "displayString" : "Last service done",
                            },
                            "lastServiceHours" : {
                                "type" : "uiFloatParam",
                                "min" : 0,
                                "name" : "lastServiceHours",
                                "displayString" : "At hours (hrs)",
                            },
                            "lastServiceOdo" : {
                                "type" : "uiFloatParam",
                                "min" : 0,
                                "name" : "lastServiceOdo",
                                "displayString" : "And at Odometer (kms)",
                            },
                            "serviceIntervalMonths" : {
                                "type" : "uiFloatParam",
                                "min" : 0,
                                "name" : "serviceIntervalMonths",
                                "displayString" : "Service Interval (months)",
                            },
                            "serviceIntervalHours" : {
                                "type" : "uiFloatParam",
                                "min" : 0,
                                "name" : "serviceIntervalHours",
                                "displayString" : "Service Interval (hrs)",
                            },
                            "serviceIntervalOdo" : {
                                "type" : "uiFloatParam",
                                "min" : 0,
                                "name" : "serviceIntervalOdo",
                                "displayString" : "Service Interval (kms)",
                            },
                            "nextServiceDue" : {
                                "type" : "uiVariable",
                                "varType" : "text",
                                "name" : "nextServiceDue",
                                "displayString" : "Next Service due (max)",
                            },
                            "nextServiceHours" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "nextServiceHours",
                                "displayString" : "At hours (hrs)",
                            },
                            "nextServiceOdo" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "nextServiceOdo",
                                "displayString" : "And at Odometer (kms)",
                            }
                        }
                    },
                    "config_submodule": {
                        "type": "uiSubmodule",
                        "name": "config_submodule",
                        "displayString": "Config",
                        "children": {
                            "setHours" : {
                                "type" : "uiFloatParam",
                                "name" : "setHours",
                                "displayString" : "Set Machine Hours (hrs)",
                            },
                            "setKms" : {
                                "type" : "uiFloatParam",
                                "name" : "setKms",
                                "displayString" : "Set Odometer (km)",
                            },
                            "warningSmsPeriod" : {
                                "type" : "uiFloatParam",
                                "name" : "warningSmsPeriod",
                                "displayString" : "SMS Alert Period (days)",
                            },
                            "aveCalcDays" : {
                                "type" : "uiFloatParam",
                                "name" : "aveCalcDays",
                                "displayString" : "Ave Use Calculation (days)",
                            }
                        }
                    },
                    "details_submodule": {
                        "type": "uiSubmodule",
                        "name": "details_submodule",
                        "displayString": "Details",
                        "children": {
                            "sysVoltage" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "sysVoltage",
                                "displayString" : "System Voltage (V)",
                                "decPrecision": 1,
                                "ranges": [
                                    {
                                        "label" : "Low",
                                        "min" : 9,
                                        "max" : 11.5,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    },
                                    {
                                        # "label" : "Ok",
                                        "min" : 11.5,
                                        "max" : 13.0,
                                        "colour" : "blue",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Charging",
                                        "min" : 13.0,
                                        "max" : 14.2,
                                        "colour" : "green",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Over Voltage",
                                        "min" : 14.2,
                                        "max" : 15.0,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    }
                                ]
                            },
                            "battVoltage" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "battVoltage",
                                "displayString" : "Tracker Battery (V)",
                                "decPrecision": 1,
                                "ranges": [
                                    {
                                        "label" : "Low",
                                        "min" : 3.0,
                                        "max" : 3.7,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    },
                                    {
                                        # "label" : "Ok",
                                        "min" : 3.7,
                                        "max" : 4.2,
                                        "colour" : "blue",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Good",
                                        "min" : 4.2,
                                        "max" : 4.7,
                                        "colour" : "green",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Over Voltage",
                                        "min" : 4.7,
                                        "max" : 5.2,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    }
                                ]
                            },
                            "gpsAccuracy" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "gpsAccuracy",
                                "displayString" : "GPS accuracy (m)",
                                "decPrecision": 0,
                                "ranges": [
                                    {
                                        "label" : "Good",
                                        "min" : 0,
                                        "max" : 15,
                                        "colour" : "green",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Ok",
                                        "min" : 15,
                                        "max" : 30,
                                        "colour" : "blue",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Bad",
                                        "min" : 30,
                                        "max" : 80,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Lost",
                                        "min" : 80,
                                        "max" : 100,
                                        "colour" : "red",
                                        "showOnGraph" : True
                                    }
                                ]
                            },
                            "dataSignalStrength" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "dataSignalStrength",
                                "displayString" : "Cellular Signal (%)",
                                "decPrecision": 0,
                                "ranges": [
                                    {
                                        "label" : "Low",
                                        "min" : 0,
                                        "max" : 30,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Ok",
                                        "min" : 30,
                                        "max" : 60,
                                        "colour" : "blue",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Strong",
                                        "min" : 60,
                                        "max" : 100,
                                        "colour" : "green",
                                        "showOnGraph" : True
                                    }
                                ]
                            },
                            "deviceTemp" : {
                                "type" : "uiVariable",
                                "varType" : "float",
                                "name" : "deviceTemp",
                                "displayString" : "Device Temperature (C)",
                                "decPrecision": 0,
                                "ranges": [
                                    {
                                        "label" : "Low",
                                        "min" : 0,
                                        "max" : 20,
                                        "colour" : "blue",
                                        "showOnGraph" : True
                                    },
                                    {
                                        # "label" : "Ok",
                                        "min" : 20,
                                        "max" : 35,
                                        "colour" : "green",
                                        "showOnGraph" : True
                                    },
                                    {
                                        "label" : "Warm",
                                        "min" : 35,
                                        "max" : 50,
                                        "colour" : "yellow",
                                        "showOnGraph" : True
                                    }
                                ]
                            },
                            "lastUplinkReason" : {
                                "type" : "uiVariable",
                                "varType" : "text",
                                "name" : "lastUplinkReason",
                                "displayString" : "Reason for uplink",
                            },
                            "deviceTimeUtc" : {
                                "type" : "uiVariable",
                                "varType" : "datetime",
                                "name" : "deviceTimeUtc",
                                "displayString" : "Device Time",
                            }
                        }
                    },
                    "dynamicHoursOffset": {
                        "type": "uiHiddenValue",
                        "name": "dynamicHoursOffset"
                    },
                    "dynamicOdoOffset": {
                        "type": "uiHiddenValue",
                        "name": "dynamicOdoOffset"
                    },
                    "prevDaysTillService": {
                        "type": "uiHiddenValue",
                        "name": "prevDaysTillService"
                    },
                    "rawRunHours": {
                        "type": "uiHiddenValue",
                        "name": "rawRunHours"
                    },
                    "rawOdometer": {
                        "type": "uiHiddenValue",
                        "name": "rawOdometer"
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

        self.ui_state_channel.publish(
            msg_str=json.dumps(ui_obj)
        )

        self.republish_dummy_msg()


    def downlink(self):
        ## Run any downlink processing code here
        
        ## Handle any new offsets that have been input
        cmds_obj = self.ui_cmds_channel.get_aggregate()

        try: dynamic_hours_offset = cmds_obj['cmds']['setHours']
        except: dynamic_hours_offset = None

        try: dynamic_odo_offset = cmds_obj['cmds']['setKms']
        except: dynamic_odo_offset = None
        
        if dynamic_hours_offset is not None or dynamic_odo_offset is not None:

            cmds = {
                "setHours" : None,
                "setKms" : None,
            }
            if dynamic_hours_offset is not None:

                ## Get the current machine hours
                ui_state_obj = self.ui_state_channel.get_aggregate()
                try: current_hours = ui_state_obj['state']['children']['deviceRunHours']['currentValue']
                except: current_hours = 0
                if current_hours is None:
                    current_hours = 0

                ## get the current offset
                current_offset = self.get_hours_offset()
                if current_offset is None:
                    current_offset = 0

                cmds['dynamicHoursOffset'] = dynamic_hours_offset - current_hours + current_offset

            if dynamic_odo_offset is not None:

                ## Get the current odo
                ui_state_obj = self.ui_state_channel.get_aggregate()
                try: current_odo = ui_state_obj['state']['children']['deviceOdometer']['currentValue']
                except: current_odo = 0
                if current_odo is None:
                    current_odo = 0

                ## get the current offset
                current_odo_offset = self.get_odo_offset()
                if current_odo_offset is None:
                    current_odo_offset = 0

                cmds['dynamicOdoOffset'] = dynamic_odo_offset - current_odo + current_odo_offset

            self.ui_cmds_channel.publish(
                msg_str=json.dumps({
                    "cmds" : cmds,
                })
            )

        self.republish_dummy_msg()


    def uplink(self):
        ## Run any uplink processing code here

        if 'msg_obj' in self.kwargs and self.kwargs['msg_obj'] is not None:
            msg_id = self.kwargs['msg_obj']['message']
            channel_id = self.kwargs['msg_obj']['channel']
            payload = self.kwargs['msg_obj']['payload']

        if not msg_id:
            self.add_to_log( "No trigger message passed - skipping processing" )
            return
        

        if not 'Records' in payload:
            self.add_to_log( "No records in payload - skipping processing" )
            return
        
        for record in payload['Records']:
            if not 'Fields' in record:
                self.add_to_log( "No fields in record - skipping processing" )
                return

            fields = record['Fields']

            device_uplink_reason = record['Reason']
            device_time_utc = record['DateUTC']
            device_time_local_str = device_time_utc
            try: 
                device_time_utc_dt = datetime.datetime.strptime(device_time_utc, '%Y-%m-%d %H:%M:%S') #2023-09-21 01:09:47 UTC
                device_time_local_str = pytz.timezone('Australia/Brisbane').fromutc(device_time_utc_dt).strftime('%d/%m/%Y %H:%M:%S')
            except:
                self.add_to_log("Error parsing device time " + str(device_time_utc) + " - " + str(traceback.format_exc()))

            position = None
            gps_accuracy_m = None
            speed_kmh = None
            ignition_on = None
            raw_run_hours = None
            device_run_hours = None
            raw_odometer = None
            device_odometer = None
            sys_voltage = None
            batt_voltage = None
            device_temp = None
            data_signal_strength = None


            for f in fields:

                if not 'FType' in f:
                    continue

                if f['FType'] == 0:
                    gps_accuracy_m = 99
                    if f['Lat'] != 0 and f['Long'] != 0:
                        position = {
                            'lat': f['Lat'],
                            'long': f['Long'],
                            'alt': f['Alt'],
                        }
                        speed_kmh = f['Spd'] * ( 3.6 / 100)
                        gps_accuracy_m = f['PosAcc']

                if f['FType'] == 2:
                    ignition_on = (f['DIn'] & 0b001 != 0)

                if f['FType'] == 6:
                    batt_voltage = f['AnalogueData']['1'] / 1000
                    sys_voltage = f['AnalogueData']['2'] / 100
                    device_temp = f['AnalogueData']['3'] / 100
                    data_signal_strength = round( f['AnalogueData']['4'] * (100/31) ) ## Signal quality between 0-31

                if f['FType'] == 27:
                    raw_odometer = f['Odo'] / 100
                    device_odometer = raw_odometer

                    raw_run_hours = f['RH'] / (60 * 60)
                    device_run_hours = raw_run_hours

                    odometer_offset = self.get_odo_offset()
                    machine_hours_offset = self.get_hours_offset()

                    if odometer_offset is not None:
                        self.add_to_log("Applying odometer offset of " + str(odometer_offset))
                        device_odometer = device_odometer + odometer_offset

                    if machine_hours_offset is not None:
                        self.add_to_log("Applying machine hours offset of " + str(machine_hours_offset))
                        device_run_hours = device_run_hours + machine_hours_offset

            if position is not None:
                self.location_channel.publish(
                    msg_str=json.dumps(position),
                    save_log=True
                )

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

            ave_rates = self.get_average_rates(raw_run_hours, device_run_hours, raw_odometer, device_odometer, self.get_average_use_window_days())

            next_service_est_dt = self.get_next_service_estimate(device_run_hours, device_odometer, ave_rates['run_hours'], ave_rates['odometer'])
            
            next_service_date = self.get_next_service_date()
            next_service_hours = self.get_next_service_hours()
            next_service_kms = self.get_next_service_kms()

            next_service_date_str = None
            if next_service_date is not None:
                # next_service_date_str = pytz.timezone('Australia/Brisbane').fromutc(next_service_date).strftime('%d/%m/%Y')
                next_service_date_str = next_service_date.strftime('%d/%m/%Y')

            hours_till_next_service = None
            if next_service_hours is not None and device_run_hours is not None:
                hours_till_next_service = next_service_hours - device_run_hours

            kms_till_next_service = None
            if next_service_kms is not None and device_odometer is not None:
                kms_till_next_service = next_service_kms - device_odometer

            next_service_est = None
            service_warning = None
            days_till_service_due = None
            prev_days_till_service = None
            if next_service_est_dt is not None:
                next_service_est = pytz.timezone('Australia/Brisbane').fromutc(next_service_est_dt).strftime('%d/%m/%Y')

                prev_days_till_service = self.get_prev_days_till_service()
                days_till_service_due, service_warning = self.assess_warnings(next_service_est_dt, prev_days_till_service)

            days_till_service_due_disp = None
            if days_till_service_due is not None:
                days_till_service_due_disp = int(days_till_service_due)

            prev_days_till_service = days_till_service_due


            self.ui_state_channel.publish(
                msg_str=json.dumps({
                    "state" : {
                        "displayString" : display_string,
                        "statusIcon" : status_icon,
                        "children" : {
                            "serviceDueWarning" : service_warning,
                            "location" : {
                                "currentValue" : position,
                            },
                            "deviceRunHours" : {
                                "currentValue" : device_run_hours,
                            },
                            "deviceOdometer" : {
                                "currentValue" : device_odometer,
                            },
                            "nextServiceEst" : {
                                "currentValue" : next_service_est,
                            },
                            "daysTillNextService" : {
                                "currentValue" : days_till_service_due_disp,
                            },
                            "smsServiceAlert": {
                                "displayString": ("Text me " + str(self.get_sms_alert_days()) + " days before next service")
                            },
                            "hoursTillNextService" : {
                                "currentValue" : hours_till_next_service,
                            },
                            "kmsTillNextService" : {
                                "currentValue" : kms_till_next_service,
                            },
                            "aveHoursPerDay" : {
                                "currentValue": ave_rates['run_hours'],
                            },
                            "aveKmsPerDay" : {
                                "currentValue": ave_rates['odometer'],
                            },
                            "ignitionOn" : {
                                "currentValue" : ignition_on,
                            },
                            "speed" : {
                                "currentValue" : speed_kmh,
                            },
                            "maintenance_submodule" : {
                                "children": {
                                    "nextServiceDue" : {
                                        "currentValue" : next_service_date_str,
                                    },
                                    "nextServiceHours" : {
                                        "currentValue" : next_service_hours,
                                    },
                                    "nextServiceOdo" : {
                                        "currentValue" : next_service_kms,
                                    },
                                }
                            },
                            "config_submodule" : {},
                            "details_submodule" : {
                                "children": {
                                    "gpsAccuracy" : {
                                        "currentValue" : gps_accuracy_m,
                                    },
                                    "sysVoltage" : {
                                        "currentValue" : sys_voltage,
                                    },
                                    "battVoltage" : {
                                        "currentValue" : batt_voltage,
                                    },
                                    "dataSignalStrength" : {
                                        "currentValue" : data_signal_strength,
                                    },
                                    "deviceTemp" : {
                                        "currentValue" : device_temp,
                                    },
                                    "lastUplinkReason" : {
                                        "currentValue" : self.uplink_reason_translate(device_uplink_reason),
                                    },
                                    "deviceTimeUtc" : {
                                        "currentValue" : device_time_local_str,
                                    }
                                }
                            },
                            "prevDaysTillService": {
                                "currentValue": prev_days_till_service,
                            },
                            "rawRunHours": {
                                "currentValue": raw_run_hours,
                            },
                            "rawOdometer": {
                                "currentValue": raw_odometer,
                            }
                        }
                    }
                }),
                save_log=True
            )

    def republish_dummy_msg(self):
        ## Publish a dummy message to oem_uplink to trigger a new process of data
        oem_uplink_channel_agg = self.oem_uplink_channel.get_aggregate()
        self.oem_uplink_channel.publish(
            msg_str=json.dumps(oem_uplink_channel_agg),
            save_log=False,
            log_aggregate=False
        )

    def get_hours_offset(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        settings_offset = self.get_agent_settings('MACHINE_HOURS_OFFSET')
        if settings_offset is not None:
            self.add_to_log("Applying settings hours offset of " + str(settings_offset))
            return settings_offset
        try: dynamic_offset = cmds_obj['cmds']['dynamicHoursOffset']
        except: dynamic_offset = None
        if dynamic_offset is not None:
            self.add_to_log("Applying dynamic hours offset of " + str(dynamic_offset))
            return dynamic_offset
        return 0
    
    def get_odo_offset(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        settings_offset = self.get_agent_settings('ODO_OFFSET')
        if settings_offset is not None:
            self.add_to_log("Applying settings odo offset of " + str(settings_offset))
            return settings_offset
        try: dynamic_offset = cmds_obj['cmds']['dynamicOdoOffset']
        except: dynamic_offset = None
        if dynamic_offset is not None:
            self.add_to_log("Applying dynamic odo offset of " + str(dynamic_offset))
            return dynamic_offset
        return 0

    def get_sms_alert_days(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return cmds_obj['cmds']['warningSmsPeriod']
        except: return 14

    def get_average_use_window_days(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return cmds_obj['cmds']['aveCalcDays']
        except: return 14

    def get_last_service_date(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return datetime.datetime.fromtimestamp( cmds_obj['cmds']['lastServiceDate'] )
        except: return None

    def get_last_service_hours(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return float(cmds_obj['cmds']['lastServiceHours'])
        except: return None

    def get_last_service_kms(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return float(cmds_obj['cmds']['lastServiceOdo'])
        except: return None

    def get_service_interval_months(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return cmds_obj['cmds']['serviceIntervalMonths']
        except: return None

    def get_service_interval_hours(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return cmds_obj['cmds']['serviceIntervalHours']
        except: return None

    def get_service_interval_kms(self):
        cmds_obj = self.ui_cmds_channel.get_aggregate()
        try: return cmds_obj['cmds']['serviceIntervalOdo']
        except: return None
    
    def get_next_service_date(self):
        last_service_date = self.get_last_service_date()
        if last_service_date is None:
            return None

        service_interval_months = self.get_service_interval_months()
        if service_interval_months is None:
            return None
        
        try:
            # return last_service_date + datetime.timedelta(months=service_interval_months)
            return last_service_date + relativedelta(months=service_interval_months)
        except Exception as e:
            self.add_to_log("Error calculating next service date " + str(e))
            return None
    
    def get_next_service_hours(self):
        last_service_hours = self.get_last_service_hours()
        if last_service_hours is None:
            return None
        
        service_interval_hours = self.get_service_interval_hours()
        if service_interval_hours is None:
            return None
        
        next_service_hours = last_service_hours + service_interval_hours
        return next_service_hours
    
    def get_next_service_kms(self):
        last_service_kms = self.get_last_service_kms()
        if last_service_kms is None:
            return None
        
        service_interval_kms = self.get_service_interval_kms()
        if service_interval_kms is None:
            return None
        
        next_service_kms = last_service_kms + service_interval_kms
        return next_service_kms

    def get_prev_days_till_service(self):
        state_obj = self.ui_state_channel.get_aggregate()
        try: return state_obj['state']['children']['prevDaysTillService']['currentValue']
        except: return None
    
    def get_next_service_estimate(self, curr_hours, device_odometer, ave_run_hours, ave_odometer):
        next_service_est_hours = None
        next_service_est_kms = None
        next_service_est_date = self.get_next_service_date()

        if curr_hours is not None and ave_run_hours is not None and self.get_next_service_hours() is not None:
            hours_to_run = self.get_next_service_hours() - curr_hours
            days_to_run = hours_to_run / ave_run_hours
            next_service_est_hours = datetime.datetime.now() + datetime.timedelta(days=days_to_run)

        if device_odometer is not None and ave_odometer is not None and self.get_next_service_kms() is not None:
            kms_to_run = self.get_next_service_kms() - device_odometer
            days_to_run = kms_to_run / ave_odometer
            next_service_est_kms = datetime.datetime.now() + datetime.timedelta(days=days_to_run)

        results = [ next_service_est_hours, next_service_est_kms, next_service_est_date ]
        self.add_to_log("Service estimates = " + str(results) + " for " + str(curr_hours) + " hours and " + str(device_odometer) + " kms")

        results = [ r for r in results if r is not None ]
        if len(results) > 0:
            selected = min(results)
            return selected
        return None

    def get_average_rates(self, raw_curr_hours, curr_hours, raw_curr_odo, curr_odo, window_days, recursive_count=2, init_hrs_per_day=None, init_kms_per_day=None):

        window_start = int( (datetime.datetime.now() - datetime.timedelta(days=window_days)).timestamp() )
        window_end = int( (datetime.datetime.now() - datetime.timedelta(days=(window_days-0.3))).timestamp() )
        
        self.add_to_log("Searching for messages between " + str(window_start) + " to " + str(window_end))
        
        messages = self.ui_state_channel.get_messages_in_window(window_start, window_end)

        hours_per_day = init_hrs_per_day
        kms_per_day = init_kms_per_day

        for m in messages:
            payload = m.get_payload()
            if payload is not None:
                if hours_per_day is None:
                    raw_run_hours = None
                    run_hours = None

                    ## try using raw hours first
                    try: 
                        raw_run_hours = payload['state']['children']['rawRunHours']['currentValue']
                    except: 
                        self.add_to_log("No rawRunHours in message payload " + str(m.message_id))
                        try: run_hours = payload['state']['children']['deviceRunHours']['currentValue']
                        except: self.add_to_log("No deviceRunHours in message payload " + str(m.message_id))

                    if raw_run_hours is not None:
                        self.add_to_log("found raw run hours = " + str(raw_run_hours))
                        hours_per_day = (raw_curr_hours - raw_run_hours) / window_days
                    elif run_hours is not None:
                        self.add_to_log("found run hours = " + str(run_hours))
                        hours_per_day = (curr_hours - run_hours) / window_days

                if kms_per_day is None:
                    raw_odometer = None
                    odometer = None

                    ## try using raw odo first
                    try: raw_odometer = payload['state']['children']['rawOdometer']['currentValue']
                    except: 
                        self.add_to_log("No rawOdometer in message payload " + str(m.message_id))
                        try: odometer = payload['state']['children']['deviceOdometer']['currentValue']
                        except: self.add_to_log("No deviceOdometer in message payload " + str(m.message_id))

                    if raw_odometer is not None:
                        self.add_to_log("found raw odometer = " + str(raw_odometer))
                        kms_per_day = (raw_curr_odo - raw_odometer) / window_days
                    elif odometer is not None:
                        self.add_to_log("found initial odometer = " + str(odometer))
                        kms_per_day = (curr_odo - odometer) / window_days

        if recursive_count > 0 and (hours_per_day is None or kms_per_day is None):
            self.add_to_log("No deviceRunHours in any messages in window " + str(window_start) + " to " + str(window_end) + ". Running recursively")
            return self.get_average_rates(raw_curr_hours, curr_hours, raw_curr_odo, curr_odo, window_days/2, recursive_count=recursive_count-1, init_hrs_per_day=hours_per_day, init_kms_per_day=kms_per_day)

        return {
            'run_hours' : hours_per_day,
            'odometer' : kms_per_day
        }
    
    def assess_warnings(self, next_service_est_dt, prev_days_till_service):

        if next_service_est_dt is None:
            self.add_to_log("No next service estimate - skipping warnings")
            return

        curr_dt = datetime.datetime.now()
        time_to_service_days = (next_service_est_dt - curr_dt) / datetime.timedelta(days=1)
        self.add_to_log("Time to service = " + str(time_to_service_days) + " days")

        warning_days = self.get_sms_alert_days()
        service_warning = None
        if time_to_service_days <= warning_days:

            warning_msg = "Service due in " + str(int(time_to_service_days)) + " days"
            if time_to_service_days < 0:
                warning_msg = "Service overdue"

            service_warning = {
                "type": "uiWarningIndicator",
                "name": "serviceDueWarning",
                "displayString": warning_msg
            }

            last_notification_age = self.get_last_notification_age()

            if (prev_days_till_service is None or prev_days_till_service > warning_days) and (last_notification_age is None or last_notification_age > (48 * 60 * 60)):
                self.add_to_log("Sending SMS alert")

                ## record the last notification time to prevent multiple notifications
                self.set_last_notification_time()

                days_till_service = int(time_to_service_days)
                if days_till_service > 0:
                    msg = "Service is due in " + str(days_till_service) + " days"
                elif days_till_service == 0:
                    msg = "Service is due today"
                else:
                    msg = "Service is overdue by " + str(abs(days_till_service)) + " days"

                self.notifications_channel.publish(
                    msg_str=msg
                )
                self.recent_activity_channel.publish(
                    msg_str=json.dumps({
                        "activity_log" : {
                            "action_string" : msg
                        }
                    })
                )

        return time_to_service_days, service_warning

    def set_last_notification_time(self, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())
        self.last_notification_time = timestamp

    def get_internal_last_notification_age(self):
        if hasattr(self, 'last_notification_time') and self.last_notification_time is not None:
            return int(int(time.time()) - self.last_notification_time)
        return None
        
    def get_last_notification_age(self):

        internal_last_notification_age = self.get_internal_last_notification_age()
        if internal_last_notification_age is not None:
            return internal_last_notification_age

        notifications_messages = self.notifications_channel.get_messages()

        last_notification_age = None
        if len(notifications_messages) > 0:
            try:
                last_notif_message = notifications_messages[0].update()
                last_notification_age = last_notif_message['current_time'] - last_notif_message['timestamp']
            except Exception as e:
                self.add_to_log("Could not get age of last notification - " + str(e))
                pass  

        return last_notification_age

    def uplink_reason_translate(self, reason_code):
        reasons = {
            0 :	'Reserved',
            1 :	'Start of trip',
            2 :	'End of trip',
            3 :	'Elapsed time',
            4 :	'Speed change',
            5 :	'Heading change',
            6 :	'Distance travelled',
            7 :	'Maximum Speed',
            8 :	'Stationary',
            9 :	'Ignition Changed',
            10 : 'Output Changed',
            11 : 'Heartbeat',
            12 : 'Harsh Brake ',
            13 : 'Harsh Acceleration',
            14 : 'Harsh Cornering',
            15 : 'External Power Change  ',
            16 : 'System Power Monitoring',
            17 : 'Driver ID Tag Read',
            18 : 'Over speed',
            19 : 'Fuel sensor record',
            20 : 'Towing Alert',
            21 : 'Debug',
            22 : 'SDI-12 sensor data',
            23 : 'Accident',
            24 : 'Accident Data',
            25 : 'Sensor value elapsed time',
            26 : 'Sensor value change',
            27 : 'Sensor alarm',
            28 : 'Rain Gauge Tipped',
            29 : 'Tamper Alert',
            30 : 'BLOB notification',
            31 : 'Time and Attendance',
            32 : 'Trip Restart',
            33 : 'Tag Gained',
            34 : 'Tag Update',
            35 : 'Tag Lost',
            36 : 'Recovery Mode On',
            37 : 'Recovery Mode Off',
            38 : 'Immobiliser On',
            39 : 'Immobiliser Off',
            40 : 'Garmin FMI Stop Response ',
            41 : 'Lone Worker Alarm',
            42 : 'Device Counters',
            43 : 'Connected Device Data',
            44 : 'Entered Geo-Fence ',
            45 : 'Exited Geo-Fence ',
            46 : 'High-G Event',
            47 : 'Third party data record',
            48 : 'Duress',
            49 : 'Cell Tower Connection',
            50 : 'Bluetooth Tag Data',
        }

        if reason_code in reasons:
            return reasons[reason_code]
        else:
            return "Unknown reason"


    def create_doover_client(self):
        self.cli = pd.doover_iface(
            agent_id=self.kwargs['agent_id'],
            access_token=self.kwargs['access_token'],
            endpoint=self.kwargs['api_endpoint'],
        )

    def get_agent_settings(self, filter_key=None):
        output = None
        if 'agent_settings' in self.kwargs and 'deployment_config' in self.kwargs['agent_settings']:
            output = self.kwargs['agent_settings']['deployment_config']

        if filter_key is not None:
            if output is not None and filter_key in output and output[filter_key] is not None:
                output = output[filter_key]
                self.add_to_log("Found agent setting for " + str(filter_key) + " = " + str(output))
                return output
            return None

        return output

    def add_to_log(self, msg):
        if not hasattr(self, '_log'):
            self._log = ""
        self._log = self._log + str(msg) + "\n"

    def complete_log(self):
        if hasattr(self, '_log') and self._log is not None:
            log_channel = self.cli.get_channel( channel_id=self.kwargs['log_channel'] )
            log_channel.publish(
                msg_str=self._log
            )
