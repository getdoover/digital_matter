#!/usr/bin/env python3

import json, logging, argparse, asyncio, signal, grpc

from .grpc_stubs import camera_iface_pb2, camera_iface_pb2_grpc    


class camera_iface:

    def __init__(self, camera_iface_uri="127.0.0.1:50055"):
        self.camera_iface_uri = camera_iface_uri

    def get_camera_snapshot(self, camera_uri, channel_name, snapshot_type='mp4', snapshot_length=6):
        try:
            snapshot_length = int(snapshot_length)
            with grpc.insecure_channel(self.camera_iface_uri) as channel:
                stub = camera_iface_pb2_grpc.cameraIfaceStub(channel)
                response = stub.RunSnapshot(camera_iface_pb2.SnapshotRequest(
                    rtsp_uri=camera_uri, 
                    output_channel=channel_name, 
                    snapshot_type=snapshot_type, 
                    snapshot_length=snapshot_length
                ))
                return response
        except Exception as e:
            logging.error("Error getting camera snapshot: " + str(e))
            return None
        


# if __name__ == "__main__":

#     logging.basicConfig(level=logging.DEBUG)
#     iface = camera_iface()
#     iface.get_camera_snapshot(
#         camera_uri="rtsp://192.168.50.120:554/s0",
#         channel_name="test",
#     )