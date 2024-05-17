#!/usr/bin/env python3

import time

from doover_docker import app_base, app_manager, run_app


class hello_world(app_base):

    def setup(self):
        super().setup()
        self.log("Hello World Setup")
        self.counter = 0
        self.subscribe_to_channel("hello_world", self.recv_channel)

    def main_loop(self):
        super().main_loop()
        self.log("Hello World Loop")
        self.counter += 1

        if self.counter < 10:
            msg = str("Hello World " + str(self.counter))
            self.log("Publishing to channel : " + msg)
            self.publish_to_channel("hello_world", msg)
            print(self.get_do(1))
        else:
            self.log("Done publishing to channel")

        time.sleep(5)

    def recv_channel(self, channel_name, payload):
        self.log("Received data on channel " + channel_name + " : " + str(payload))



if __name__ == "__main__":

    new_app = hello_world()



    run_app(new_app)