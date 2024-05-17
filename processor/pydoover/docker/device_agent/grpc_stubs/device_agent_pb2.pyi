from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ResponseHeader(_message.Message):
    __slots__ = ("success", "cloud_synced", "response_code", "response_message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CLOUD_SYNCED_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_CODE_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    cloud_synced: bool
    response_code: int
    response_message: str
    def __init__(self, success: bool = ..., cloud_synced: bool = ..., response_code: _Optional[int] = ..., response_message: _Optional[str] = ...) -> None: ...

class MessageDetails(_message.Message):
    __slots__ = ("message_id", "channel_name", "payload", "timestamp")
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    channel_name: str
    payload: str
    timestamp: str
    def __init__(self, message_id: _Optional[str] = ..., channel_name: _Optional[str] = ..., payload: _Optional[str] = ..., timestamp: _Optional[str] = ...) -> None: ...

class ChannelDetails(_message.Message):
    __slots__ = ("channel_name", "aggregate")
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    AGGREGATE_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    aggregate: str
    def __init__(self, channel_name: _Optional[str] = ..., aggregate: _Optional[str] = ...) -> None: ...

class AgentDetails(_message.Message):
    __slots__ = ("agent_id", "agent_name", "channels")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    agent_name: str
    channels: _containers.RepeatedCompositeFieldContainer[ChannelDetails]
    def __init__(self, agent_id: _Optional[str] = ..., agent_name: _Optional[str] = ..., channels: _Optional[_Iterable[_Union[ChannelDetails, _Mapping]]] = ...) -> None: ...

class TestCommsRequest(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class TestCommsResponse(_message.Message):
    __slots__ = ("response_header", "response")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    response: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., response: _Optional[str] = ...) -> None: ...

class MessageDetailsRequest(_message.Message):
    __slots__ = ("message_id",)
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    message_id: str
    def __init__(self, message_id: _Optional[str] = ...) -> None: ...

class MessageDetailsResponse(_message.Message):
    __slots__ = ("response_header", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message: MessageDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message: _Optional[_Union[MessageDetails, _Mapping]] = ...) -> None: ...

class ChannelDetailsRequest(_message.Message):
    __slots__ = ("channel_name",)
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    def __init__(self, channel_name: _Optional[str] = ...) -> None: ...

class ChannelDetailsResponse(_message.Message):
    __slots__ = ("response_header", "channel")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    channel: ChannelDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., channel: _Optional[_Union[ChannelDetails, _Mapping]] = ...) -> None: ...

class ChannelSubscriptionRequest(_message.Message):
    __slots__ = ("channel_name",)
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    def __init__(self, channel_name: _Optional[str] = ...) -> None: ...

class ChannelSubscriptionResponse(_message.Message):
    __slots__ = ("response_header", "channel", "message")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    channel: ChannelDetails
    message: MessageDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., channel: _Optional[_Union[ChannelDetails, _Mapping]] = ..., message: _Optional[_Union[MessageDetails, _Mapping]] = ...) -> None: ...

class ChannelWriteRequest(_message.Message):
    __slots__ = ("channel_name", "message_payload", "save_log")
    CHANNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SAVE_LOG_FIELD_NUMBER: _ClassVar[int]
    channel_name: str
    message_payload: str
    save_log: bool
    def __init__(self, channel_name: _Optional[str] = ..., message_payload: _Optional[str] = ..., save_log: bool = ...) -> None: ...

class ChannelWriteResponse(_message.Message):
    __slots__ = ("response_header", "message_id")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_ID_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    message_id: str
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., message_id: _Optional[str] = ...) -> None: ...

class AgentDetailsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class AgentDetailsResponse(_message.Message):
    __slots__ = ("response_header", "agent")
    RESPONSE_HEADER_FIELD_NUMBER: _ClassVar[int]
    AGENT_FIELD_NUMBER: _ClassVar[int]
    response_header: ResponseHeader
    agent: AgentDetails
    def __init__(self, response_header: _Optional[_Union[ResponseHeader, _Mapping]] = ..., agent: _Optional[_Union[AgentDetails, _Mapping]] = ...) -> None: ...
