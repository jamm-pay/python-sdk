"""Enum constants and comparison helpers.

REST responses and webhook payloads carry enums as strings (``"ERROR_TYPE_AUTH_FAILED"``),
while the generated protobuf enums are ints. These helpers compare one against the other
so callers never hand-write the wire strings:

    if jamm.types.error_type_equals(jamm.types.ErrorType.ERROR_TYPE_KYC_REJECTED, err.error_type):
        ...

Both sides accept either form -- an int enum value or its full name.

Names must match exactly. Prefix-stripped short names ("KYC_REJECTED") are deliberately
NOT accepted: suffix matching cannot distinguish a constant from a sibling that ends with
it, so ``"AUTHORIZED"`` would match ``PAYMENT_AUTHORIZATION_STATUS_NOT_AUTHORIZED`` and
read a declined authorization as approved. Pass the enum constant, or the full wire name.
"""

from typing import Union

from lib.proto.api.v1.common_pb2 import (
    ContractStatus,
    DepositType,
    KycStatus,
    PaymentAuthorizationStatus,
)
from lib.proto.api.v1.merchant_webhooks_pb2 import ChargeMessage, EventType
from lib.proto.api.v1.payment_pb2 import OnSessionPaymentErrorCode
from lib.proto.error.v1.error_pb2 import ErrorType

# Nested enums, surfaced at module level so callers need not reach through the message.
ChargeMessageStatus = ChargeMessage.Status
ChargeMessageApiSource = ChargeMessage.ApiSource

EnumValue = Union[int, str]


def _name(enum, value: EnumValue) -> str:
    """Resolve a value to a known member name, or "" when it is not one.

    Both forms are validated against the enum descriptor. Returning an unrecognized
    string unchanged would make two identical unknown names compare equal --
    ``event_type_equals("EVENT_TYPE_FUTURE", "EVENT_TYPE_FUTURE")`` was True -- which
    contradicts the documented behaviour that an unknown value matches nothing.
    """
    if isinstance(value, bool):
        # bool is an int subclass, and no enum is keyed by True/False.
        raise TypeError(f"expected an enum value or name, got {value!r}")

    if isinstance(value, int):
        try:
            return enum.Name(value)
        except ValueError:
            # An unknown numeric value cannot match any known name.
            return ""

    if isinstance(value, str):
        return value if value in enum.DESCRIPTOR.values_by_name else ""

    return ""


def _equals(enum, expected: EnumValue, given: EnumValue) -> bool:
    """Compare two enum representations by exact name.

    Suffix tolerance is intentionally absent: no substring rule can tell a constant
    apart from a sibling ending with the same word, and for negated pairs like
    AUTHORIZED / NOT_AUTHORIZED a false positive inverts the caller's decision.
    """
    left = _name(enum, expected)
    right = _name(enum, given)

    if not left or not right:
        return False

    return left == right


def error_type_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same ErrorType as `expected`."""
    return _equals(ErrorType, expected, given)


def deposit_type_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same DepositType as `expected`."""
    return _equals(DepositType, expected, given)


def kyc_status_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same KycStatus as `expected`."""
    return _equals(KycStatus, expected, given)


def payment_authorization_status_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same PaymentAuthorizationStatus as `expected`."""
    return _equals(PaymentAuthorizationStatus, expected, given)


def contract_status_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same ContractStatus as `expected`."""
    return _equals(ContractStatus, expected, given)


def charge_message_status_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same ChargeMessage.Status as `expected`."""
    return _equals(ChargeMessageStatus, expected, given)


def api_source_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same ChargeMessage.ApiSource as `expected`.

    ``api_source`` identifies which API created the charge and is present on charge
    and refund webhooks. This SDK creates charges via ``off_session_async`` and
    ``on_session``; the remaining members are still decodable, since a webhook may
    describe a charge this SDK did not create.
    """
    return _equals(ChargeMessageApiSource, expected, given)


def event_type_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same webhook EventType as `expected`."""
    return _equals(EventType, expected, given)


def on_session_payment_error_code_equals(expected: EnumValue, given: EnumValue) -> bool:
    """Whether `given` denotes the same OnSessionPaymentErrorCode as `expected`."""
    return _equals(OnSessionPaymentErrorCode, expected, given)


__all__ = [
    # Enums
    "ErrorType",
    "DepositType",
    "KycStatus",
    "PaymentAuthorizationStatus",
    "ContractStatus",
    "ChargeMessageStatus",
    "ChargeMessageApiSource",
    "EventType",
    "OnSessionPaymentErrorCode",
    # Comparison helpers
    "error_type_equals",
    "deposit_type_equals",
    "kyc_status_equals",
    "payment_authorization_status_equals",
    "contract_status_equals",
    "charge_message_status_equals",
    "api_source_equals",
    "event_type_equals",
    "on_session_payment_error_code_equals",
]
