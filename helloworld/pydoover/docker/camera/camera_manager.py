import time, logging, asyncio, traceback

from pydoover.ui.ui_elements import doover_ui_camera
from .camera import camera_iface


def dict_get(input_dict, key, case_sensitive=False):
    if not case_sensitive:
        return input_dict.get(key, None)

    result = input_dict.get(key, None)
    if result is not None: return result
    
    result = input_dict.get(key.upper(), None)
    return result


class camera:

    def __init__(self, cam_dict):
        self.cam_dict = cam_dict

    def __eq__(self, other):
        return other is not None and isinstance(other, self.__class__) and self.cam_dict == other.cam_dict

    def get_name(self):
        result = dict_get(self.cam_dict, 'NAME')
        if result is None:
            result = "camera"
        return result.lower().replace(' ', '_')

    def get_display_name(self):
        result = dict_get(self.cam_dict, 'DISPLAY_NAME')
        if result is None:
            result = dict_get(self.cam_dict, 'NAME')
        return result

    def get_uri(self):
        return dict_get(self.cam_dict, 'URI')
    
    def get_mode(self):
        result = dict_get(self.cam_dict, 'MODE')
        if result is None:
            result = "mp4"
        return result

    def get_snapshot_secs(self):
        result = dict_get(self.cam_dict, 'SNAPSHOT_SECS')
        if result is None:
            result = 6
        return result

    def get_wake_delay(self):
        result = dict_get(self.cam_dict, 'wake_delay')
        if result is None:
            result = 10
        return result

    def trigger_snapshot(self, camera_iface):
        camera_iface.get_camera_snapshot(
            camera_uri=self.get_uri(),
            channel_name=self.get_name(),
            snapshot_type=self.get_mode(),
            snapshot_length=self.get_snapshot_secs()
        )


## CONFIG WILL LOOK LIKE THE FOLLOWING
#
# {
#     "camera_config": {
#         "power_pin" : 1,
#         "cameras": {
#             "cam_1" : {
#                 "name": "cam_1",
#                 "display_name": "Camera 1",
#                 "uri": "rtsp://192.168.50.120:544",
#                 "mode": "mp4",
#                 "snapshot_secs": 6
#             },
#             "cam_2" : {

#             }
#         }
#     }
# }




class camera_manager:
    
    def __init__(
                self,
                camera_config=None,
                config_manager=None,
                dda_iface=None,
                ui_manager=None,
                plt_iface=None,
                app_manager=None,
                is_active=True,
            ):
        self.camera_config = camera_config
        self.config_manager = config_manager
        self.dda_iface = dda_iface
        self.ui_manager = ui_manager
        self.plt_iface = plt_iface
        self.app_manager = app_manager

        self.is_active = is_active

        self.last_camera_snapshot = time.time()
        self.iter_counter = 0
        self.snapshot_task = None

        self.camera_snap_cmd_name = "camera_snapshots"
        self.last_snapshot_cmd_name = "last_cam_snapshot"

    def get_camera_config(self):
        if self.config_manager is not None:
            return self.config_manager.get_config('camera_config')
        else:
            return self.camera_config

    def get_is_active(self):
        if not self.is_active:
            return False
        if self.get_camera_config() is None:
            return False
        return True

    def get_camera_snapshot_period(self):
        if not self.get_is_active():
            return None
        config = self.get_camera_config()
        try:
            return config['SNAPSHOT_PERIOD']
        except KeyError:
            logging.warning("Unable to parse camera snapshot period from config")
        return None
    
    def get_cameras(self):
        config = self.get_camera_config()
        if not "CAMERAS" in config:
            return None
        
        result = []
        for c in config['CAMERAS']:
            cam_dict = config['CAMERAS'][c]
            result.append(
                camera(
                    cam_dict=cam_dict,
                )
            )
        return result

    def get_ui_elements(self):
        if not self.get_is_active():
            return None
        result = []
        cameras = self.get_cameras()
        if cameras is None:
            return None
        for c in cameras:
            result.append(
                doover_ui_camera(
                    name=c.get_name(),
                    display_str=c.get_display_name(),
                    uri=c.get_uri(),
                )
            )
        return result

    def update_ui_elements(self):
        if self.get_is_active() and self.ui_manager is not None:
            cams = self.get_ui_elements()
            self.ui_manager.add_children(cams)

    def setup(self):
        if self.ui_manager is not None:
            self.ui_manager.add_cmds_update_subscription(self.check_snapshot_cmd)

    def main_loop(self):
        self.iter_counter += 1
        if self.iter_counter > 999999999:
            self.iter_counter = 0

        if self.iter_counter % 10 == 0: ## Only check if cameras overdue on every 10th cycle
            self.assess_snapshot_due()

        self.update_ui_elements()
    
    def assess_snapshot_due(self):
        if not self.get_is_active():
            return False
        if self.snapshot_task is not None:
            return False ## Snapshot currently running
        snap_period = self.get_camera_snapshot_period()
        if snap_period is None:
            return False
        if time.time() - self.last_camera_snapshot > snap_period:
            self.trigger_all_snapshots()
            return True
        return False

    def check_snapshot_cmd(self):
        last_snap_cmd = self.ui_manager.get_command(self.last_snapshot_cmd_name)
        if last_snap_cmd is not None:
            self.last_camera_snapshot = last_snap_cmd

        snap_cmd = self.ui_manager.get_command(self.camera_snap_cmd_name)
        if snap_cmd is not None:
            self.ui_manager.coerce_command(self.camera_snap_cmd_name, None)

            if self.snapshot_task is None: # If task not already running
                self.trigger_all_snapshots()

    def set_last_snapshot_time(self, ts=None):
        ts = ts or time.time()

        self.last_camera_snapshot = ts
        self.ui_manager.coerce_command(self.last_snapshot_cmd_name, ts)

    def trigger_all_snapshots(self):
        if self.snapshot_task is None:
            self.set_last_snapshot_time()
            self.snapshot_task = self.app_manager.start_task(self.run_all_snapshots_task)

    async def run_all_snapshots_task(self):
        try:
            cameras = self.get_cameras()
            if len(cameras) < 1:
                raise Exception("No cameras defined")

            for c in cameras:
                c.trigger_snapshot(self.app_manager.get_camera_iface())

            logging.info("Camera take all snapshots complete")

        except Exception as e:
            logging.error("Error in camera snapshot task : " + str(e))
            logging.error(traceback.format_exc())

        self.snapshot_task = None
