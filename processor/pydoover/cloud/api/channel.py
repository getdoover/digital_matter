import base64
import os
import shutil
import uuid

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .client import Client


class Channel:

    def __init__(self, *, client, data):
        self.client: "Client" = client
        self._messages = None

        self._from_data(data)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def _from_data(self, data):
        self.id = data["channel"]
        self.name = data["name"]
        # from the get_agent endpoint this is `agent`, from the get_channel endpoint this is `owner`.
        self.agent_id = (data.get("owner") or data.get("agent"))
        self._agent = None

        try:
            self.aggregate = data["aggregate"]["payload"]
        except KeyError:
            self.aggregate = None

    def update(self):
        res = self.client._get_channel_raw(self.id)
        self._from_data(res)

    def fetch_agent(self):
        if self._agent is not None:
            return self._agent

        self._agent = self.client.get_agent(self.agent_id)
        return self._agent

    def fetch_messages(self):
        if self._messages is not None:
            return self._messages

        self._messages = self.client.get_channel_messages(self.id)
        return self._messages

    def publish(self, data: Any, save_log: bool = True, log_aggregate: bool = False):
        return self.client.publish_to_channel(self.id, data, save_log, log_aggregate)


class Processor(Channel):
    def update_from_package(self, package_dir):
        fp = f"/tmp/{uuid.uuid4()}"
        shutil.make_archive(fp, 'zip', package_dir)

        with open(f"{fp}.zip", "rb") as f:
            zip_bytes = f.read()
            b64_package = base64.b64encode(zip_bytes).decode()

        self.publish(b64_package)
        os.remove(f"{fp}.zip")


class Task(Channel):
    def _from_data(self, data):
        super()._from_data(data)
        self.processor_id: str = data.get("processor")
        self._processor = None

    def fetch_processor(self) -> Optional[Processor]:
        if self._processor is not None:
            return self._processor
        if self.processor_id is None:
            return

        self._processor = self.client.get_channel(self.processor_id)
        return self._processor

    def subscribe_to_channel(self, channel_id: str):
        return self.client.subscribe_to_channel(channel_id, self.id)

    def unsubscribe_from_channel(self, channel_id: str):
        return self.client.unsubscribe_from_channel(channel_id, self.id)
