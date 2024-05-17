#!/usr/bin/env python3

import json, copy, time, logging

from .ui_elements import *


class log_manager:

    # def __init__(self, min_period_secs, min_observed_period_secs):
    def __init__(self, min_period_secs):
        
        self.min_period_secs = min_period_secs
        # self.min_observed_period_secs = min_observed_period_secs

        self.last_critical_values = {}
        self.log_required = True
        self.last_log_time = time.time()

    def set_min_period_secs(self, min_period):
        self.min_period_secs = min_period

    # def set_min_observed_period_secs(self, min_period):
    #     self.min_observed_period_secs = min_period

    def add_critical_value(self, name, value):
        if name in list(self.last_critical_values.keys()):
            last_val = self.last_critical_values[name]
            if last_val != value:
                logging.debug("Recorded different critical value : " + str(name) + " = " + str(value))
                self.log_required = True
        else:
            self.log_required = True

        self.last_critical_values[name] = value

    def record_log_sent(self):
        self.log_required = False
        self.last_log_time = time.time()

    def is_log_required(self, is_being_observed=False):
    # def is_log_required(self):
        if self.log_required:
            return True

        min_period = self.min_period_secs
        # if is_being_observed:
        #     min_period = self.min_observed_period_secs

        if time.time() - self.last_log_time > min_period:
            return True
        
        return False



class ui_manager:
    
    def __init__(self, agent_id=None, dda_iface=None, auto_start=False):

        self.dda_iface = dda_iface
        self.agent_id = agent_id

        self.dda_subscriptions_ready = False

        self.last_ui_state = None ## A python dictionary of the full state from the cloud
        self.last_ui_state_update = None

        self.last_ui_state_wss_connections = None
        self.last_ui_state_wss_connections_update = None

        self.last_ui_cmds = None
        self.last_ui_cmds_update = None

        self.cmd_coercions_to_apply = dict() ## A dict of changes to make to the next published desired state

        self.base_container = doover_ui_container(
            name=None, # name=self.agent_id,
            display_str=None, # display_str=self.agent_id
        )

        self.min_ui_update_period_secs = 4
        self.last_ui_update_sent = None

        self.log_manager = log_manager( min_period_secs=600 )

        # self.channel_subscriptions = {} # A dictionary of lists, each channel_name with a list of callbacks to call
        self.cmds_subscriptions = []

        if auto_start:
            self.start_comms()

    def start_comms(self):
        self.setup_dda_subscriptions()

    def check_dda(self, setup=False):
        if self.dda_iface is None or not self.dda_subscriptions_ready:
            if setup:
                self.setup_dda_subscriptions()
            else:
                logging.error("Attempted use of dda_iface in ui_manager without dda_iface being ready")

    def setup_dda_subscriptions(self):
        if self.dda_iface is not None:
            logging.info("Setting up dda subscriptions")
            self.dda_iface.add_subscription("ui_state", self.recv_channel_update)
            self.dda_iface.add_subscription("ui_state@wss_connections", self.recv_channel_update)
            self.dda_iface.add_subscription("ui_cmds", self.recv_channel_update)

            self.dda_subscriptions_ready = True
        else:
            logging.warning("Attempted to setup dda subscriptions without dda_iface being set")

    def add_cmds_update_subscription(self, callback):
        self.cmds_subscriptions.append(callback)

    def recv_channel_update(self, channel_name, aggregate):
        if channel_name == "ui_state":
            self.last_ui_state = aggregate
            self.last_ui_state_update = time.time()
        if channel_name == "ui_state@wss_connections":
            self.last_ui_state_wss_connections = aggregate
            self.last_ui_state_wss_connections_update = time.time()
        if channel_name == "ui_cmds":
            self.last_ui_cmds = aggregate
            self.last_ui_cmds_update = time.time()

            ## call all subscribed to cmds updates
            for c in self.cmds_subscriptions:
                c()
    
    def send_alert(self, topic, message):
        self.check_dda() 
        self.dda_iface.publish_to_channel(topic, message)

    def send_crash_log(self, message):
        self.check_dda()
        self.dda_iface.publish_to_channel("crash_logs", message)
    
    def set_display_str(self, disp_str):
        self.base_container.set_display_str(disp_str)

    def get_available_commands(self):
        available_cmds = []

        if self.last_ui_cmds is not None and 'cmds' in self.last_ui_cmds:
            for k in self.last_ui_cmds['cmds'].keys():
                available_cmds.append(k)

        return available_cmds

    def get_command(self, name):
        if self.last_ui_cmds is None or 'cmds' not in self.last_ui_cmds:
            return None

        cmd = None

        if name in self.last_ui_cmds['cmds']:
            cmd = self.last_ui_cmds['cmds'][name]

        ## Check if coerced command requires clearing
        found_coerced_cmd = False
        if name in self.cmd_coercions_to_apply:
            coerced_cmd = self.cmd_coercions_to_apply[name]
            found_coerced_cmd = True

        if found_coerced_cmd:
            if coerced_cmd == cmd: ## If the coerced command is equal to the cmd retreived from the downloaded state, this coercion has been applied and is now defunct - remove it
                self.cmd_coercions_to_apply.pop( name )
            else:
                cmd = coerced_cmd

        return cmd

    def coerce_command(self, name, value):
        self.cmd_coercions_to_apply[name] = value

    def get_is_connected(self):
        self.check_dda()
        return self.dda_iface.get_is_dda_online()

    def is_being_observed(self):
        if self.last_ui_state_wss_connections is not None:
            if "connections" in self.last_ui_state_wss_connections and isinstance(self.last_ui_state_wss_connections["connections"], dict):
                connections = self.last_ui_state_wss_connections["connections"]

                ## if there is more than one connection, then we are being observed
                if len(connections.keys()) > 1:
                    return True

                ## The following isn't working currently as agent_id is None
                # for k in connections.keys():
                #     if k != self.agent_id and connections[k] is True:
                #         return True
        return False

    def get_has_been_connected(self):
        if self.dda_iface is not None:
            return self.dda_iface.get_has_dda_been_online()
        return not self.last_ui_state == None

    def set_min_send_period(self, min_period_secs):
        self.log_manager.set_min_period_secs( min_period=min_period_secs )

    def set_min_observed_send_period(self, min_period_secs):
        self.log_manager.set_min_observed_period_secs( min_period=min_period_secs )

    def record_critical_value(self, name, value):
        self.log_manager.add_critical_value(name=name, value=value)

    def handle_comms(self, force_log=False):        
        
        log_required = (self.log_manager.is_log_required() or force_log)

        observed_reading_required = self.is_being_observed()
        if self.last_ui_update_sent is None or ((time.time() - self.last_ui_update_sent) < self.min_ui_update_period_secs):
            observed_reading_required = False

        if log_required or observed_reading_required:

            self.send_update(record_log=log_required)
            self.last_ui_update_sent = time.time()
            if log_required:
                self.log_manager.record_log_sent()


    def get_cmds_update(self):
        ## Create the desired state update
        if self.last_ui_cmds is not None and 'cmds' in self.last_ui_cmds:
            downloaded_cmds = self.last_ui_cmds['cmds']
        else:
            downloaded_cmds = dict()
        cmds_update = copy.copy(downloaded_cmds)

        # remove any unnecessary keys from the desired state
        keys_to_remove = []
        required_keys = self.get_ui_interaction_keys()
        for k in downloaded_cmds.keys():
            if k not in required_keys:
                keys_to_remove.append( k )
        for k in keys_to_remove:
            cmds_update[k] = None

        # update any commands that required coercing
        for key, value in self.cmd_coercions_to_apply.items():
            cmds_update[key] = value

        # remove any unchanged values from the desired state update to reduce size
        keys_to_remove = []
        for k in cmds_update.keys():
            if k in downloaded_cmds:
                if downloaded_cmds[k] == cmds_update[k]:
                    keys_to_remove.append(k)
        for k in keys_to_remove:
            del cmds_update[k]

        if len(cmds_update.keys()) == 0:
            cmds_update = None

        return cmds_update


    def send_update(self, record_log=True):
        self.check_dda()

        if not self.get_is_connected(): ## Must have downloaded the last state first before sending
            return False

        cmds_update = self.get_cmds_update()
        if cmds_update is not None:
            
            ui_cmds_msg = {"cmds" : cmds_update}
            result = self.dda_iface.publish_to_channel(
                "ui_cmds",
                ui_cmds_msg
            ) 

        ui_state_update = self.get_ui_state_update()
        if ui_state_update is not None:

            result = self.dda_iface.publish_to_channel(
                "ui_state",
                ui_state_update,
                record_log,
            )

        return True        

    def get_ui_interaction_keys(self):
        keys = []

        ## A Recursively called function
        def traverse_children(obj):
            children = []
            if hasattr(obj, 'get_children'):
                chlds = obj.get_children()
                for c in chlds:
                    res_chlds = traverse_children( c )
                    for rc in res_chlds:
                        children.append(rc)
                    children.append(c)
            return children

        all_children = traverse_children( self.base_container )

        for c in all_children:

            if (isinstance(c, doover_ui_interaction) or 
                isinstance(c, doover_ui_hidden_value) or 
                isinstance(c, doover_ui_warning_indicator)):

                keys.append(c.get_name())

        return keys

    def clear_ui(self):
        logging.info("Clearing UI")
        self.base_container.set_children([])
        self.send_update(record_log=False)

    def set_children(self, children):
        self.base_container.set_children( children )
        # self.base_container.add_children( self.cameras )
        # if len(self.cameras) > 0:
        #     self.base_container.add_children( [ doover_ui_hidden_value(name="last_cam_snapshot") ] )

    def set_status_icon(self, icon_type):
        self.base_container.set_status_icon( icon_type )

    def add_children(self, children):
        for c in children:
            self.base_container.add_child( c )

    def add_submodule(self, name, display_str, is_available=None, help_str=None, status_string=None, collapsed=False):
        new_submodule = doover_ui_submodule(
            name=name,
            display_str=display_str,
            is_available=is_available,
            help_str=help_str,
            status_string=status_string,
            collapsed=collapsed
        )

        self.base_container.add_child( new_submodule )

        return new_submodule

    def get_ui_state_dict(self):
        reported_dict = self.base_container.get_as_dict()
        # reported_dict['device_timestamp'] = str(time.time())
        return reported_dict

    def get_reported_state_string(self):
        return json.dumps( self.get_ui_state_dict() )

    def get_ui_state_update(self):
        ui_state_dict = self.get_ui_state_dict()
        last_ui_state = self.last_ui_state

        if ui_state_dict is None:
            ui_state_dict = {}
        if last_ui_state is None:
            last_ui_state = {}

        new_ui_state = {"state": ui_state_dict}

        # logging.debug("Last UI State: " + str(last_ui_state))
        # logging.debug("New UI State: " + str(new_ui_state))

        update = ui_manager.get_json_update(last_ui_state, new_ui_state)
        
        # logging.debug("UI State Update: " + str(update))

        if len(update.keys()) == 0:
            return None
        
        return update

    @staticmethod
    def get_json_update(input_obj, desired_output):

        if isinstance(input_obj, dict) and isinstance(desired_output, dict):
            ## Merge the two dictionaries
            merged = {**input_obj, **desired_output}
            output = copy.copy(merged)
            for k in merged.keys():
                if k not in desired_output.keys():
                    output[k] = None
                elif k not in input_obj.keys():
                    if merged[k] == None:
                        del output[k]
                    else:
                        pass ## Just move on and leave output as the desired	
                elif isinstance(output[k], dict):
                    result = ui_manager.get_json_update(input_obj[k], desired_output[k])
                    if result == {}:
                        del output[k]
                    else:
                        output[k] = result
                elif input_obj[k] != desired_output[k]:
                    output[k] = desired_output[k]
                else:
                    del output[k]
            return output
        elif input_obj == desired_output:
            return {}
        else:
            return desired_output
        

