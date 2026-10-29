from api.v1 import merchant_webhooks_pb2 as _merchant_webhooks_pb2
from buf.validate import validate_pb2 as _validate_pb2
from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from protoc_gen_openapiv2.options import annotations_pb2 as _annotations_pb2_1
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WebhookEndpointStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    WEBHOOK_ENDPOINT_STATUS_UNSPECIFIED: _ClassVar[WebhookEndpointStatus]
    WEBHOOK_ENDPOINT_STATUS_LIVE: _ClassVar[WebhookEndpointStatus]
    WEBHOOK_ENDPOINT_STATUS_TEST: _ClassVar[WebhookEndpointStatus]
    WEBHOOK_ENDPOINT_STATUS_DISABLED: _ClassVar[WebhookEndpointStatus]
WEBHOOK_ENDPOINT_STATUS_UNSPECIFIED: WebhookEndpointStatus
WEBHOOK_ENDPOINT_STATUS_LIVE: WebhookEndpointStatus
WEBHOOK_ENDPOINT_STATUS_TEST: WebhookEndpointStatus
WEBHOOK_ENDPOINT_STATUS_DISABLED: WebhookEndpointStatus

class WebhookEndpoint(_message.Message):
    __slots__ = ("id", "url", "status", "api_version", "previous_api_version", "promoted_at", "created_at", "updated_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    API_VERSION_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_API_VERSION_FIELD_NUMBER: _ClassVar[int]
    PROMOTED_AT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    url: str
    status: WebhookEndpointStatus
    api_version: str
    previous_api_version: str
    promoted_at: _timestamp_pb2.Timestamp
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., url: _Optional[str] = ..., status: _Optional[_Union[WebhookEndpointStatus, str]] = ..., api_version: _Optional[str] = ..., previous_api_version: _Optional[str] = ..., promoted_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateWebhookEndpointRequest(_message.Message):
    __slots__ = ("url", "api_version")
    URL_FIELD_NUMBER: _ClassVar[int]
    API_VERSION_FIELD_NUMBER: _ClassVar[int]
    url: str
    api_version: str
    def __init__(self, url: _Optional[str] = ..., api_version: _Optional[str] = ...) -> None: ...

class CreateWebhookEndpointResponse(_message.Message):
    __slots__ = ("endpoint",)
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    endpoint: WebhookEndpoint
    def __init__(self, endpoint: _Optional[_Union[WebhookEndpoint, _Mapping]] = ...) -> None: ...

class PromoteWebhookEndpointRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PromoteWebhookEndpointResponse(_message.Message):
    __slots__ = ("endpoint",)
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    endpoint: WebhookEndpoint
    def __init__(self, endpoint: _Optional[_Union[WebhookEndpoint, _Mapping]] = ...) -> None: ...

class TriggerWebhookEventRequest(_message.Message):
    __slots__ = ("event_type",)
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    event_type: _merchant_webhooks_pb2.EventType
    def __init__(self, event_type: _Optional[_Union[_merchant_webhooks_pb2.EventType, str]] = ...) -> None: ...

class TriggerWebhookEventResponse(_message.Message):
    __slots__ = ("endpoint",)
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    endpoint: WebhookEndpoint
    def __init__(self, endpoint: _Optional[_Union[WebhookEndpoint, _Mapping]] = ...) -> None: ...

class RollbackWebhookEndpointRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RollbackWebhookEndpointResponse(_message.Message):
    __slots__ = ("endpoint",)
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    endpoint: WebhookEndpoint
    def __init__(self, endpoint: _Optional[_Union[WebhookEndpoint, _Mapping]] = ...) -> None: ...
