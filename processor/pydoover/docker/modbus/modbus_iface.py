#!/usr/bin/env python3

import json, time, threading, logging, asyncio, grpc, traceback

from .grpc_stubs import modbus_iface_pb2, modbus_iface_pb2_grpc    


VALID_SERIAL_CONFIG_KEYS = (
    "SERIAL_PORT", "SERIAL_BAUD", "SERIAL_METHOD", "SERIAL_BITS", "SERIAL_PARITY", "SERIAL_STOP", "SERIAL_TIMEOUT",
)


def two_words_to_32bit_float(word1, word2, swap=False):
    if swap:
        word1, word2 = word2, word1
    return word1 + (word2 * 65536)


class modbus_iface:

    def __init__(self, modbus_uri="127.0.0.1:50054", config_manager=None):
        self.modbus_iface_uri = modbus_uri

        self.subscription_tasks = []

        self.setup_task = None
        self.config_complete = True
        if config_manager is not None:
            self.set_config_manager(config_manager=config_manager)
            self.setup_task = asyncio.get_event_loop().create_task(self.setup_from_config_manager())


    def set_config_manager(self, config_manager, run_setup=False):
        if self.setup_task is not None:
            logging.warning("Modbus Iface has already been setup, skipping new config manager setup")
        self.config_complete = False
        self.config_manager = config_manager

        if run_setup:
            self.setup_task = asyncio.get_event_loop().create_task(self.setup_from_config_manager())

    async def setup_from_config_manager(self):
        await self.config_manager.await_config()

        modbus_config = self.config_manager.get_config('MODBUS_CONFIG')
        logging.info("Setting up modbus iface with following config : " + str(modbus_config))
        if modbus_config is None:
            logging.info("No modbus config found")
            return None
        
        if "SERIAL_PORT" in modbus_config:
            config = {k.lower(): v for k, v in modbus_config.items() if k in VALID_SERIAL_CONFIG_KEYS}
            logging.info("opening new modbus bus on serial port with configuration %s", str(config))
            self.open_bus(bus_type="serial", name="default", **config)

        elif "TCP_URI" in modbus_config:
            tcp_uri = modbus_config.get("TCP_URI", None)
            tcp_timeout = modbus_config.get("TCP_TIMEOUT", None)

            logging.info("opening new tcp modbus bus on uri " + str(tcp_uri))

            self.open_bus(
                bus_type="tcp",
                name="default",
                tcp_uri=tcp_uri,
                tcp_timeout=tcp_timeout,
            )

        elif "BUSES" in modbus_config:

            logging.info("opening multiple modbus buses from config")

            for bus in modbus_config["BUSES"]:
                bus_type = bus.get("BUS_TYPE", None)
                bus_name = bus.get("BUS_NAME", None)

                if bus_type == "serial":
                    serial_port = bus.get("SERIAL_PORT", None)
                    serial_baud = bus.get("SERIAL_BAUD", None)
                    serial_method = bus.get("SERIAL_METHOD", None)
                    serial_bits = bus.get("SERIAL_BITS", None)
                    serial_parity = bus.get("SERIAL_PARITY", None)
                    serial_stop = bus.get("SERIAL_STOP", None)
                    serial_timeout = bus.get("SERIAL_TIMEOUT", None)

                    logging.info("opening new modbus bus on serial port " + str(serial_port))

                    self.open_bus(
                        bus_type="serial",
                        name=bus_name,
                        serial_port=serial_port,
                        serial_baud=serial_baud,
                        serial_method=serial_method,
                        serial_bits=serial_bits,
                        serial_parity=serial_parity,
                        serial_stop=serial_stop,
                        serial_timeout=serial_timeout,
                    )

                elif bus_type == "tcp":
                    tcp_uri = bus.get("TCP_URI", None)
                    tcp_timeout = bus.get("TCP_TIMEOUT")

                    logging.info("opening new tcp modbus bus on uri " + str(tcp_uri))

                    self.open_bus(
                        bus_type="tcp",
                        name=bus_name,
                        tcp_uri=tcp_uri,
                        tcp_timeout=tcp_timeout,
                    )
        
        else:
            logging.info("No modbus buses opened from config")

        self.config_complete = True


    def ensure_bus_availabe(self, bus_id, response_header, configure=True):
        ## if not config_complete, wait for setup to complete
        if not self.config_complete or (self.setup_task is not None and not self.setup_task.done()):
            logging.debug("Waiting for modbus setup to complete")
            return False

        ## check the bus status from the response and if the bus does not exist, and configure is True, rerun the setup
        bus_statusses = response_header.bus_status
        for b in bus_statusses:
            if b.bus_id == bus_id:
                return b.open
            
        logging.warning("Bus " + str(bus_id) + " not found in response")
        if configure:
            logging.info("Reconfiguring modbus iface")
            asyncio.run(self.setup_from_config_manager())
        
        return True


    def close(self):
        logging.info("Closing modbus interface")
        for task in self.subscription_tasks:
            task.cancel()
        

    def open_bus(
            self, 
            bus_type="serial",
            name="default",
            serial_port="/dev/ttyS0",
            serial_baud=9600,
            serial_method="rtu",
            serial_bits=8,
            serial_parity="N",
            serial_stop=1,
            serial_timeout=0.3,
            tcp_uri="127.0.0.1:5000",
            tcp_timeout=2,
        ):
        
        try:
            with grpc.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)

                if bus_type == "serial":
                    response = stub.openBus(modbus_iface_pb2.openBusRequest(
                        bus_id=name,
                        serial_settings=modbus_iface_pb2.serialBusSettings(
                            port=serial_port,
                            baud=serial_baud,
                            modbus_method=serial_method,
                            data_bits=serial_bits,
                            parity=serial_parity,
                            stop_bits=serial_stop,
                            timeout=serial_timeout,
                        )
                    ))
                elif bus_type == "tcp":
                    response = stub.openBus(modbus_iface_pb2.openBusRequest(
                        bus_type=bus_type,
                        name=name,
                        tcp_settings=modbus_iface_pb2.tcpSettings(
                            uri=tcp_uri,
                            timeout=tcp_timeout,
                        )
                    ))
                else:
                    logging.error("Invalid bus type: " + str(bus_type))
                    return None
                
                success = response.response_header.success
                if not success:
                    logging.error("Error opening modbus bus: " + response.response_header.response_message)
                return success
            
        except Exception as e:
            logging.error("Error opening modbus bus: " + str(e))
            return None


    def close_bus(
            self,
            bus_id="default",
        ):

        try:
            with grpc.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                response = stub.closeBus(modbus_iface_pb2.closeBusRequest(
                    bus_id=bus_id,
                ))

                success = response.response_header.success
                if not success:
                    logging.error("Error closing modbus bus: " + response.response_header.response_message)
                return success

        except Exception as e:
            logging.error("Error closing modbus bus: " + str(e))
            return None
    

    def getBusStatus(self, bus_id="default"):

        try:
            with grpc.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                response = stub.busStatus(modbus_iface_pb2.busStatusRequest(
                    bus_id=bus_id,
                ))

                success = response.response_header.success
                if not success:
                    logging.error("Error getting modbus bus status: " + response.response_header.response_message)
                return response.bus_status.open

        except Exception as e:
            logging.error("Error getting modbus bus status: " + str(e))
            return None


    def read_registers(
            self, 
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type=4,
            configure_bus=True,
        ):
        
        try:
            with grpc.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                response = stub.readRegisters(modbus_iface_pb2.readRegisterRequest(
                    bus_id=bus_id,
                    modbus_id=modbus_id,
                    register_type=register_type,
                    address=start_address,
                    count=num_registers,
                ))

                success = response.response_header.success
                if not success:
                    logging.error("Error reading modbus registers: " + response.response_header.response_message)
                    if configure_bus and not self.ensure_bus_availabe(bus_id, response.response_header):
                        logging.warning("Seems bus is not available")
                    return None
                values = response.values
                if len(values) == 0:
                    return None
                if len(values) == 1:
                    return values[0]
                return values

        except Exception as e:
            logging.error("Error reading modbus registers: " + str(e))
            logging.error(traceback.format_exc())
            return None


    def write_registers(
            self, 
            bus_id="default",
            modbus_id=1,
            start_address=0,
            values=[],
            register_type=4,
            configure_bus=True,
        ):
        
        try:
            with grpc.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                response = stub.writeRegisters(modbus_iface_pb2.writeRegisterRequest(
                    bus_id=bus_id,
                    modbus_id=modbus_id,
                    register_type=register_type,
                    address=start_address,
                    values=values,
                ))

                success = response.response_header.success
                if not success:
                    logging.error("Error writing modbus registers: " + response.response_header.response_message)
                    if configure_bus and not self.ensure_bus_availabe(bus_id, response.response_header):
                        logging.warning("Seems bus is not available")
                return success

        except Exception as e:
            logging.error("Error writing modbus registers: " + str(e))
            return None


    def add_read_register_subscription(
            self, 
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type=4,
            poll_secs=3,
            callback=None,
        ):

        if callback is None:
            logging.error("No callback provided for read register subscription")
            return None
        
        try:
            new_task = asyncio.get_event_loop().create_task(self.run_read_register_subscription_task(
                bus_id=bus_id,
                modbus_id=modbus_id,
                start_address=start_address,
                num_registers=num_registers,
                register_type=register_type,
                poll_secs=poll_secs,
                callback=callback,
            ))

            self.subscription_tasks.append(new_task)
            return new_task
        
        except Exception as e:
            logging.error("Error adding read register subscription: " + str(e))
            return None


    async def run_read_register_subscription_task(
            self,
            bus_id="default",
            modbus_id=1,
            start_address=0,
            num_registers=1,
            register_type=4,
            poll_secs=3,
            callback=None,
            configure_bus=True,
        ):

        try:
            async with grpc.aio.insecure_channel(self.modbus_iface_uri) as channel:
                stub = modbus_iface_pb2_grpc.modbusIfaceStub(channel)
                request = modbus_iface_pb2.readRegisterSubscriptionRequest(
                    bus_id=bus_id,
                    modbus_id=modbus_id,
                    register_type=register_type,
                    address=start_address,
                    count=num_registers,
                    poll_secs=poll_secs,
                )

                try:
                    async for response in stub.readRegisterSubscription(request):
                        
                        success = response.response_header.success
                        if not success:
                            logging.debug("Error in modbus subscription_response: " + response.response_header.response_message)
                            if configure_bus and not self.ensure_bus_availabe(bus_id, response.response_header):
                                logging.warning("Seems bus is not available")
                            values = None
                        elif len(response.values) == 1:
                            values = response.values[0]
                        else:
                            values = response.values

                        logging.debug("recieved new modbus subscription result on bus " + str(bus_id) + ", for modbus_id " + str(modbus_id) + ", result=" + str(success))
                        if callback is not None:
                            callback(values)

                except Exception as e:
                    logging.error("Error in read register subscription task: " + str(e))
                    return None
        
        except Exception as e:
            logging.error("Error in read register subscription task: " + str(e))
            return None




# async def run_test():
    
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    iface = modbus_iface()
    iface.open_bus(
        bus_type="serial",
        name="test",
        serial_port="/dev/ttyk37simOut",
        serial_baud=38400,
        serial_method="rtu",
        serial_bits=8,
        serial_parity="N",
        serial_stop=1,
        serial_timeout=0.3,
    )

    print(iface.getBusStatus(bus_id="test"))

    result = iface.read_registers(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=23,
    )
    print(result)

    watchdog = result[22] + 1

    result = iface.write_registers(
        bus_id="test",
        modbus_id=1,
        start_address=22,
        values=[watchdog],
    )

    ## define a function to print the results of read register subscription
    def print_results(values):
        print(values)

    loop = asyncio.get_event_loop()

    ## add a read register subscription
    iface.add_read_register_subscription(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=23,
        callback=print_results,
    )

    print("Subscribed to read register subscription")

    ## add a read register subscription
    iface.add_read_register_subscription(
        bus_id="test",
        modbus_id=1,
        start_address=0,
        num_registers=10,
        callback=print_results,
    )

    # async def run_test():
    #     await asyncio.sleep(20)
    #     iface.close()

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass

    logging.info("Closing modbus interface")
    iface.close()


