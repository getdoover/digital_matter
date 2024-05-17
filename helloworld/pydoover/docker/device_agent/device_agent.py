#!/usr/bin/env python3

import json, logging, argparse, asyncio, signal, grpc

from .grpc_stubs import device_agent_pb2, device_agent_pb2_grpc    


class device_agent_iface:
    
    def __init__(
            self, 
            dda_uri="127.0.0.1:50051",
            dda_timeout=7,
            max_conn_attempts=5, 
            time_between_connection_attempts=10,
        ):
        
        self.dda_uri = dda_uri
        self.dda_timeout = dda_timeout
        self.max_connection_attempts = max_conn_attempts
        self.time_between_connection_attempts = time_between_connection_attempts

        self.is_dda_available = False
        self.is_dda_online = False
        self.has_dda_been_online = False

        self.subscriptions = {}
        # this is a list of channels that the agent interface will subscribe to,
        # and a list of callbacks that will be called when a message is received,
        # as well as the aggregate data that is received from the channel
        ## for channel in default_subscriptions:
            # #self.subscriptions[channel] = {"callbacks": [], "aggregate": None, is_synced: False}

        self.subscription_handlers = []
        # this is a list of async functions that will be called when the agent interface starts a subscription

    def get_is_dda_available(self):
        return self.is_dda_available
    
    def get_is_dda_online(self):
        return self.is_dda_online
    
    def get_has_dda_been_online(self):
        return self.has_dda_been_online

    def add_subscription(self, channel_name, callback=None):
        existing_channel_subs = self.subscriptions.keys()
        if not channel_name in existing_channel_subs:
            logging.debug("Adding subscription to channel: " + channel_name)
            listener = asyncio.ensure_future(self.start_subscription_listener(channel_name))
            self.subscription_handlers += [listener]
            self.subscriptions[channel_name] = {"listener": listener, "callbacks": [], "aggregate": None, "is_synced": False}
        else:
            logging.debug("Subscription already exists for channel: " + channel_name)

        if callback is not None:
            logging.debug("Adding new callback for subscription to " + channel_name)
            self.subscriptions[channel_name]["callbacks"].append(callback)

    async def start_subscription_listener(self, channel_name):
        while True:
            try:
                logging.debug("Starting subscription to channel: " + channel_name)
                callback = self.recv_update_callback
                await self.recv_channel_msgs(channel_name, callback)
            except Exception as e:
                logging.error("Error starting subscription listener for " + str(channel_name) + ": " + str(e))
                await asyncio.sleep(self.time_between_connection_attempts)

    def recv_update_callback(self, channel_name, response):
        logging.debug("Received response from subscription request: " + str(response)[:100])
        aggregate = self.get_channel_aggregate(channel_name)
        if aggregate is not None and aggregate != "":
            
            ## validate aggregate is valid json
            try:
                json_aggregate = json.loads(aggregate)
                aggregate = json_aggregate
                logging.debug("Parsed aggregate from channel: " + channel_name + " : " + str(json_aggregate)[:100])
            except:
                logging.debug("Failed to parse aggregate from channel: " + channel_name)
            
            logging.debug("Received aggregate from channel: " + channel_name)
            self.subscriptions[channel_name]["aggregate"] = aggregate

            ## invoke all callbacks
            for callback in self.subscriptions[channel_name]["callbacks"]:
                callback(channel_name, aggregate)
        else:
            logging.warning("Failed to get aggregate from channel: " + channel_name)


    async def recv_channel_msgs(self, channel_name, callback):

        ## Setup the connection to the doover device agent (DDA)
        async with grpc.aio.insecure_channel(self.dda_uri) as channel:

            channel_stream = device_agent_pb2_grpc.deviceAgentStub(channel).GetChannelSubscription( device_agent_pb2.ChannelSubscriptionRequest(channel_name=channel_name))
            while True:
                try:
                    response = await channel_stream.read()
                    logging.debug("Received response from subscription request on " + str(channel_name) + " : " + str(response).replace("\n", " ")[:120])
                    self.update_dda_status(response.response_header)
                    if not response.response_header.success:
                        logging.error("Failed to subscribe to channel " + str(channel_name) + ": " + response.response_header.error_message)
                        return False
                    else:
                        logging.debug("Calling callback with subscription response for " + str(channel_name) + "...")
                        callback(channel_name, response)
                except StopAsyncIteration:
                    logging.debug("Channel stream ended.")
                    break
    

    def get_channel_aggregate(self, channel_name):
        with grpc.insecure_channel(self.dda_uri) as channel:
            stub = device_agent_pb2_grpc.deviceAgentStub(channel)
            response = stub.GetChannelDetails(device_agent_pb2.ChannelDetailsRequest(channel_name=channel_name), timeout=self.dda_timeout)

            self.update_dda_status(response.response_header)
            if response.response_header.success:
                return response.channel.aggregate
            else:
                return None

    def publish_to_channel(self, channel_name, message, record_log=True, save_aggregate=False):
        if isinstance(message, dict):
            message = json.dumps(message)

        try:
            with grpc.insecure_channel(self.dda_uri) as channel:
                stub = device_agent_pb2_grpc.deviceAgentStub(channel)
                response = stub.WriteToChannel(device_agent_pb2.ChannelWriteRequest(channel_name=channel_name, message_payload=message, save_log=record_log), timeout=self.dda_timeout)
                self.update_dda_status(response.response_header)
                return response.response_header.success
        except Exception as e:
            logging.error("Error attempting publish to channel : " + str(e))
            return False

    def update_dda_status(self, response_header):
        if response_header.success:
            self.is_dda_available = True
        else:
            self.is_dda_available = False

        if response_header.cloud_synced:
            self.is_dda_online = True

            if not self.has_dda_been_online:
                logging.info("Device Agent is online")
            self.has_dda_been_online = True
        else:
            self.is_dda_online = False

    def close(self):
        for listener in self.subscription_handlers:
            listener.cancel()
        logging.info("Closing device agent interface...")
    
