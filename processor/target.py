#!/usr/bin/python3
import sys
import time
import json
import traceback


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

SERIAL_AGENT_MAP_CHANNEL_NAME = "dm_agent_map"


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


    ## This function is invoked after the singleton instance is created
    def execute(self):

        start_time = time.time()

        self.create_doover_client()

        self.add_to_log( "kwargs = " + str(self.kwargs) )
        self.add_to_log( str( start_time ) )

        try:
            
            ## Do any processing you would like to do here
            message_type = None
            if 'message_type' in self.kwargs['package_config'] and 'message_type' != None:
                message_type = self.kwargs['package_config']['message_type']

            if message_type == "CONNECTOR_RECV":
                self.process_connector_message(self.kwargs['msg_obj'])
            if message_type == "SYNC_SERIAL_NUM_AGENT_IDS":
                self.sync_serial_num_agent_ids()
                return


        except Exception as e:
            self.add_to_log("ERROR attempting to process message - " + str(e))
            self.add_to_log(traceback.format_exc())

        self.complete_log()


    def process_connector_message(self, msg_obj):

        if 'payload' not in msg_obj:
            self.add_to_log( "No payload passed - skipping processing" )
            return
        if 'SerNo' not in msg_obj['payload']:
            self.add_to_log( "No serial number passed - skipping processing" )
            return
        
        serial_num = msg_obj['payload']['SerNo']

        # agents = self.cli.get_agents()
        # self.add_to_log(str(len(agents)) + " accessible agents to process")

        # for ak, a in agents.items():
        #     deployment_config = a.get_deployment_config()
        #     if deployment_config is not None and 'DM_SERIAL' in deployment_config:
        #         if serial_num == deployment_config['DM_SERIAL']:
        #             agent_key = a.get_agent_id()
        #             self.add_to_log('Found agent ' + str(agent_key) + " with matching serial number " + str(serial_num))

        channel = self.cli.get_channel(channel_name=SERIAL_AGENT_MAP_CHANNEL_NAME, agent_id=self.kwargs["agent_id"])
        aggregate = channel.get_aggregate()

        try:
            agent_key = aggregate[str(serial_num)]
        except KeyError:
            self.add_to_log(f"No agent with serial number {serial_num} found.")
            return

        self.add_to_log(f"Found agent {agent_key} (SER# {serial_num})")

        self.cli.api_client.publish_to_channel(
            msg_str=json.dumps(msg_obj['payload']),
            agent_id=agent_key,
            channel_name="dm_oem_uplink_recv"
        )

        # destination_channel = self.cli.get_channel(
        #     channel_name="dm_oem_uplink_recv",
        #     agent_id=agent_key
        # )
        #
        # destination_channel.publish(
        #     msg_str=json.dumps(msg_obj['payload'])
        # )

        self.add_to_log("Published to dm_oem_uplink_recv channel")
        return

    def sync_serial_num_agent_ids(self):
        agents = self.cli.get_agents()
        self.add_to_log(f"{len(agents)} accessible agents to process")

        lookup = {}

        for agent in agents.values():
            config = agent.get_deployment_config()
            try:
                serial_number = config["DM_SERIAL"]
            except KeyError:
                pass
            else:
                lookup[serial_number] = agent.agent_id
                self.add_to_log(f"Found agent {agent.agent_id} with matching serial number {serial_number}")

        self.add_to_log(f"Syncing serial numbers to agent keys: {lookup}")
        self.cli.api_client.publish_to_channel(json.dumps(lookup), agent_id=self.kwargs['agent_id'], channel_name=SERIAL_AGENT_MAP_CHANNEL_NAME)

    def create_doover_client(self):
        self.cli = pd.doover_iface(
            agent_id=self.kwargs['agent_id'],
            access_token=self.kwargs['access_token'],
            endpoint=self.kwargs['api_endpoint'],
        )

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
