#!/usr/bin/env python3
import threading
import time, logging, traceback, argparse, asyncio, signal, inspect

from .device_agent.device_agent import device_agent_iface
from .camera.camera_manager import camera_manager
from .camera.camera import camera_iface
from .platform.platform import platform_iface
from .modbus.modbus_iface import modbus_iface
from pydoover.ui import ui_manager


class app_manager_logging_formatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class app_base:

    def __init__(self, manager=None, name=None):
        self.manager = manager

        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name

        self.log_warnings_issued = []

    def set_manager(self, manager):
        self.manager = manager

    def get_app_name(self):
        return self.name

    def get_manager(self):
        return self.manager
    

    ## Agent Interface Functions (DDA)

    def get_agent_iface(self):
        return self.manager.get_agent_iface()
    
    def get_is_dda_available(self):
        return self.get_agent_iface().get_is_dda_available()
    
    def get_is_dda_online(self):
        return self.get_agent_iface().get_is_dda_online()
    
    def get_has_dda_been_online(self):
        return self.get_agent_iface().get_has_dda_been_online()

    def subscribe_to_channel(self, channel_name, callback=None):
        self.get_agent_iface().add_subscription(channel_name, callback)

    def publish_to_channel(self, channel_name, data):
        self.get_agent_iface().publish_to_channel(channel_name, data)

    def get_channel_aggregate(self, channel_name):
        return self.get_agent_iface().get_channel_aggregate(channel_name)
    

    ## Config Manager Functions

    def get_config_manager(self):
        return self.manager.get_config_manager()
    
    def get_config(self, key_filter=None, wait=None):
        return self.get_config_manager().get_config(key_filter, wait)


    ## UI Manager Functions

    def get_ui_manager(self):
        if not hasattr(self, "ui_manager"):
            self.ui_manager = ui_manager(
                agent_id=None,
                dda_iface=self.get_agent_iface()
            )
        return self.ui_manager
    
    def set_ui_elements(self, elements):
        return self.get_ui_manager().set_children(elements)

    def get_command(self, name):
        return self.get_ui_manager().get_command(name)
    
    def coerce_command(self, name, value):
        return self.get_ui_manager().coerce_command(name, value)
    
    def record_critical_value(self, name, value):
        return self.get_ui_manager().record_critical_value(name, value)

    def set_ui_status_icon(self, icon):
        return self.get_ui_manager().set_status_icon(icon)

    def start_ui_comms(self):
        ui_manager_obj = self.get_ui_manager()
        ui_manager_obj.start_comms()

    def set_ui(self, ui):
        self.get_ui_manager().set_children(ui)

    def update_ui(self):
        self.get_ui_manager().handle_comms()


    ## Platform Interface Functions

    def get_platform_iface(self):
        return self.get_manager().get_platform_iface()
    
    def get_di(self, di):
        return self.get_platform_iface().get_di(di)

    def get_ai(self, ai):
        return self.get_platform_iface().get_ai(ai)

    def get_do(self, do):
        return self.get_platform_iface().get_do(do)
    
    def set_do(self, do, value):
        return self.get_platform_iface().set_do(do, value)
    
    def schedule_do(self, do, value, delay_secs):
        return self.get_platform_iface().schedule_do(do, value, delay_secs)
    
    def get_ao(self, ao):
        return self.get_platform_iface().get_ao(ao)

    def set_ao(self, ao, value):
        return self.get_platform_iface().set_ao(ao, value)
    
    def schedule_ao(self, ao, value, delay_secs):
        return self.get_platform_iface().schedule_ao(ao, value, delay_secs)
    

    ## Modbus Interface Functions

    def get_modbus_iface(self):
        return self.get_manager().get_modbus_iface()
    
    def read_modbus_registers(self, address, count, register_type, modbus_id=None, bus_id=None):
        return self.get_modbus_iface().read_registers(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            num_registers=count,
            register_type=register_type,
        )
    
    def write_modbus_registers(self, address, values, register_type, modbus_id=None, bus_id=None):
        return self.get_modbus_iface().write_registers(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            values=values,
            register_type=register_type,
        )
    
    def add_new_modbus_read_subscription(self, address, count, register_type, callback, poll_secs=None, modbus_id=None, bus_id=None):
        return self.get_modbus_iface().add_new_read_subscription(
            bus_id=bus_id, 
            modbus_id=modbus_id, 
            start_address=address,
            num_registers=count,
            register_type=register_type,
            poll_secs=poll_secs,
            callback=callback,
        )


    ## Camera Manager Functions

    def get_camera_manager(self):
        if not hasattr(self, "camera_manager"):
            logging.info("Creating camera manager")
            self.camera_manager = camera_manager(
                config_manager=self.get_config_manager(),
                dda_iface=self.get_agent_iface(),
                ui_manager=self.get_ui_manager(),
                plt_iface=self.get_platform_iface(),
                app_manager=self.get_manager(),
            )
        return self.camera_manager


    ## App Functions

    def setup(self):
        logging.info("Setting up app : " + self.get_app_name())

        self.start_ui_comms()
        self.get_camera_manager().setup()
        

    def main_loop(self):
        logging.info("Running main_loop : " + self.get_app_name())

        self.get_camera_manager().main_loop()
        self.update_ui()
        

    def log(self, log_level="info", msg=None):

        ## Allows multiple variants of arguments to be accepted as valid
        if msg is None and log_level is not None:
            msg = log_level
            log_level = None

        if log_level not in ["debug", "info", "warning", "error", "critical"]:
            if log_level not in self.log_warnings_issued:
                logging.warning("Invalid log level '" + str(log_level) + "' , defaulting to 'info'")
                self.log_warnings_issued.append(log_level)
            log_level = "info"
        log_function = getattr(logging, log_level)
        log_function("[" + self.get_app_name() + "] " + str(msg))



class deployment_config_manager:


    def __init__(self, dda_iface=None, auto_start=True):
        self.dda_iface = dda_iface
        
        self.deployment_channel_name = 'deployment_config'

        self.is_subscribed = False
        self.has_recv_message = False
        self.last_deployment_config = {}

        if auto_start and self.dda_iface is not None:
            self.setup()


    def set_dda_iface(self, dda_iface):
        self.dda_iface = dda_iface


    def setup(self):
        if self.is_subscribed:
            return ## already setup

        self.is_subscribed = True
        self.dda_iface.add_subscription(self.deployment_channel_name, self.recv_updates)


    async def await_config(self, wait_period=20):
        logging.info("Awaiting deployment config...")
        self.setup()
        wait_start = time.time()
        while not self.has_recv_message and ((time.time() - wait_start) < wait_period):
            await asyncio.sleep(0.25)

        if self.has_recv_message:
            logging.info("Received deployment config")
        else:
            logging.warning("Failed to receive deployment config")

        return self.last_deployment_config


    def recv_updates(self, channel_name, last_aggregate):
        if channel_name is not self.deployment_channel_name:
            return ## Not the correct channel - something weird here
        
        if 'deployment_config' not in last_aggregate:
            logging.info("No deployment_config field in last deployment_config channel aggregate")
            return
        self.last_deployment_config = last_aggregate['deployment_config']
        logging.debug("Received deployment config: " + str(self.last_deployment_config))

        self.has_recv_message = True


    def get_config(self, key_filter=None, wait=True, wait_period=10, case_sensitive=False):
        if wait and not self.has_recv_message:
            wait_start = time.time()
            while not self.has_recv_message and (time.time() - wait_start < wait_period):
                time.sleep(0.25)

        if self.last_deployment_config is None or len(self.last_deployment_config.keys()) == 0:
            return None            

        if key_filter is None:
            return self.last_deployment_config

        result = self.last_deployment_config
        if not isinstance(key_filter, list):
            key_filter = [key_filter]

        for search_key in key_filter:
            keys = list(result.keys())
            orig_keys = keys
            
            if not case_sensitive:
                keys = [k.lower() if isinstance(k, str) else k for k in keys]
                search_key = search_key.lower()

            if search_key in keys:
                key_index = keys.index(search_key)
                orig_key = orig_keys[key_index]
                result = result[orig_key]
            else:
                result = None
                break

        logging.debug("Config for " + str(key_filter) + ": " + str(result))
        return result


class app_manager:

    def __init__(
            self, 
            loop_obj=None, 
            device_agent=None, 
            platform_iface=None,
            modbus_iface=None,
            camera_iface=None, 
        ):
        self.loop_obj = loop_obj
        self.device_agent = device_agent
        self.platform_iface = platform_iface
        self.modbus_iface = modbus_iface
        self.camera_iface = camera_iface

        self.restart_all_on_error = True
        self.error_wait_period = 10
        self.should_stop = False
        self.setup_functions = []
        self.loop_functions = []

        if self.loop_obj is None:
            self.create_loop()
        if self.device_agent is None:
            self.device_agent = device_agent_iface()

        self.config_manager = deployment_config_manager(dda_iface=self.device_agent)

        if self.platform_iface is None:
            self.platform_iface = platform_iface()


    def register_loop(self, callable):
        self.loop_functions.append(callable)

    def register_setup_function(self, callable):
        self.setup_functions.append(callable)


    async def main_loop(self):

        ## ensure config is recieved before starting
        await self.config_manager.await_config()

        ## trigger modbus iface setup
        self.modbus_iface.set_config_manager(self.config_manager)
        await self.modbus_iface.setup_from_config_manager()

        while not self.should_stop:
            restart_loop = False

            for setup in self.setup_functions:
                try:
                    if inspect.iscoroutinefunction(setup):
                        await setup()
                    else:
                        setup()
                except Exception as e:
                    logging.error("Error in setup function: " + str(e))
                    # logging.error("Setup: " + str(setup))
                    logging.error(traceback.format_exc())
                    if self.restart_all_on_error:
                        logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before closing app\n\n")
                    else:
                        logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before restarting app\n\n")
                    await asyncio.sleep(self.error_wait_period)
                    
                    restart_loop = True
                    break

            ## allow for other async tasks to run between setup and loop
            await asyncio.sleep(0.2)

            while not self.should_stop and not restart_loop:
                for loop in self.loop_functions:
                    try:
                        if inspect.iscoroutinefunction(loop):
                            await loop()
                        else:
                            await asyncio.get_event_loop().run_in_executor(None, loop)
                            # loop()
                    except Exception as e:
                        logging.error("Error in loop function: " + str(e))
                        # logging.error("Loop: " + str(loop))
                        logging.error(traceback.format_exc())
                        if self.restart_all_on_error:
                            logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before closing app\n\n")
                        else:
                            logging.warning("\n\n\nWaiting " + str(self.error_wait_period) + " seconds before restarting app\n\n")
                        await asyncio.sleep(self.error_wait_period)

                        restart_loop = True
                        break

                ## Allow for other async tasks to run
                await asyncio.sleep(0.2)

            if self.restart_all_on_error:
                self.close()
                return

    def start_task(self, function):
        thread = threading.Thread(target=asyncio.run, args=(function(), ))
        thread.start()
        return thread

    def create_loop(self):
        if self.loop_obj is None:
            self.loop_obj = asyncio.get_event_loop()
            
            self.loop_obj.add_signal_handler(signal.SIGINT, self.close)
            self.loop_obj.add_signal_handler(signal.SIGTERM, self.close)

            asyncio.set_event_loop(self.loop_obj)

    def get_loop(self):
        return self.loop_obj
    
    def get_agent_iface(self):
        return self.device_agent
    
    def get_config_manager(self):
        return self.config_manager
    
    def get_config(self, key_filter, wait=True):
        return self.get_config_manager().get_config(key_filter=key_filter, wait=wait)

    def get_platform_iface(self):
        return self.platform_iface
    
    def get_modbus_iface(self):
        return self.modbus_iface
    
    def get_camera_iface(self):
        return self.camera_iface

    def run(self):
        try:
            self.loop_obj.run_until_complete(self.main_loop())
        except asyncio.CancelledError:
            logging.info("Main loop cancelled")
        except Exception as e:
            logging.error("Error in main loop: " + str(e))
            logging.error(traceback.format_exc())

    def close(self):
        if not self.should_stop:
            logging.info("\n########################################\n\nClosing app manager...\n\n########################################\n")
            self.should_stop = True
            if self.device_agent is not None:
                self.device_agent.close()

            def stop_loop():
                loop_obj = asyncio.get_event_loop()
                tasks = asyncio.all_tasks(loop_obj)
                for task in tasks:
                    task.cancel()
                # loop_obj.stop()

            self.loop_obj.call_soon_threadsafe(stop_loop)



def run_app(app, dda_iface=None, plt_iface=None, mb_iface=None, cam_iface=None, debug=False):

    parser = argparse.ArgumentParser(description='Doover Docker App Manager')

    parser.add_argument('--remote-dev', type=str, default=None, help='Remote device URI')
    parser.add_argument('--dda-uri', type=str, default="localhost:50051", help='Doover Device Agent URI')
    parser.add_argument('--plt-uri', type=str, default="localhost:50053", help='Platform Interface URI')
    parser.add_argument('--modbus-uri', type=str, default="localhost:50054", help='Modbus Interface URI')
    parser.add_argument('--cam-uri', type=str, default="localhost:50055", help='Camera Interface URI')
    parser.add_argument('--dds-sys-sock', type=str, default="/var/lib/dds/dds_sys.sock", help='DDS System Socket File Path')
    parser.add_argument('--debug', action='store_true', default=False, help='Debug Mode')

    args = parser.parse_args()

    if args.debug or debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(app_manager_logging_formatter())
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(handler)


    dda_uri = args.dda_uri
    plt_uri = args.plt_uri
    modbus_uri = args.modbus_uri
    cam_uri = args.cam_uri

    if args.remote_dev is not None:
        dda_uri = args.dda_uri.replace("localhost", args.remote_dev)
        plt_uri = args.plt_uri.replace("localhost", args.remote_dev)
        modbus_uri = args.modbus_uri.replace("localhost", args.remote_dev)
        cam_uri = args.cam_uri.replace("localhost", args.remote_dev)

    if dda_iface is None:
        dda_iface = device_agent_iface(
            dda_uri=dda_uri,
        )

    if plt_iface is None:
        plt_iface = platform_iface(
            plt_uri=plt_uri,
        )

    if mb_iface is None:
        mb_iface = modbus_iface(
            modbus_uri=modbus_uri,
        )

    if cam_iface is None:
        cam_iface = camera_iface(
            camera_iface_uri=cam_uri,
        )

    app_manager_obj = app_manager(
        device_agent=dda_iface,
        platform_iface=plt_iface,
        modbus_iface=mb_iface,
        camera_iface=cam_iface,
    )
    app.set_manager(app_manager_obj)

    app_manager_obj.register_setup_function(app.setup)
    app_manager_obj.register_loop(app.main_loop)
    app_manager_obj.run()



if __name__ == "__main__":

    run_app(app_base())