# jamm_sdk/webhook.py
import hashlib
import hmac
import json
import re
from collections.abc import Mapping
from typing import Any, Dict, Optional, Union

from . import types

# ========== Exception Classes ==========


class InvalidSignatureError(Exception):
    """Raised when webhook signature verification fails"""

    pass


# ========== Enum coercion ==========

# The backend serializes webhook payloads with Go's json.Marshal (not protojson), so
# enum fields arrive as their integer wire value while the REST API returns the string
# constant. Coerce integers to the string form so both transports read alike, matching
# the Ruby SDK.


# Safe because protojson never emits consecutive capitals: APIVersion would
# split to a_p_i_version.
_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")

# The merchant's own map: rewriting orderRef to order_ref would corrupt it.
_VERBATIM_KEYS = frozenset({"metadata"})


def _to_snake_keys(value: Any) -> Any:
    """Rewrite camelCase keys to snake_case so either wire shape parses.

    A cut moves payloads to camelCase; the SDK cannot ask which is coming.
    """
    if isinstance(value, list):
        return [_to_snake_keys(item) for item in value]
    if not isinstance(value, dict):
        return value

    # Both spellings of one field cannot arrive together; last would win.
    out = {}
    for key, nested in value.items():
        if not isinstance(key, str):
            out[key] = nested
            continue
        snake = _CAMEL_BOUNDARY.sub("_", key).lower()
        out[snake] = nested if snake in _VERBATIM_KEYS else _to_snake_keys(nested)
    return out


def _coerce_enum(enum, value: Any) -> Any:
    """Map a numeric enum wire value onto its string constant.

    A value that is already a string (REST-style) passes through untouched, as does
    None. An unrecognized number is also passed through verbatim: rewriting it to the
    zero constant would report a future event or status as ``*_UNSPECIFIED``, which is
    indistinguishable from a genuinely unspecified one, so an operator debugging a
    dropped event could not see which type was dropped. Callers comparing through
    ``jamm.types`` are unaffected -- an unknown value matches no constant either way.
    """
    if value is None or isinstance(value, str):
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return enum.Name(value)
        except ValueError:
            return value

    return value


# ========== Webhook Message Classes ==========


class _RawDataMapping(Mapping):
    """Read-only mapping over the raw payload a typed webhook object was built from.

    Before 0.8.0 these fields were the raw dicts the backend sent, so callers read them
    with ``error["code"]``, ``.get``, ``in``, ``len``, ``.items()`` and looped over them.
    Typing them would have broken all of that on upgrade. Implementing the Mapping
    protocol -- rather than hand-picking a few dict methods -- keeps every one of those
    working, including the ones easy to forget: iteration, ``items()``/``values()``,
    ``len()``, truthiness of an empty payload and ``==`` against a plain dict.
    """

    def __init__(self, data: Dict[str, Any]):
        self._raw_data = data

    def __getitem__(self, key):
        return self._raw_data[key]

    def __iter__(self):
        return iter(self._raw_data)

    def __len__(self):
        return len(self._raw_data)


class ChargeError(_RawDataMapping):
    """An error attached to a failed charge or refund (equivalent to Error)"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.code = data.get("code")
        self.message = data.get("message")
        self.details = data.get("details")

    def __repr__(self):
        return f"ChargeError(code={self.code})"


class RefundInfo(_RawDataMapping):
    """Refund details, present on refund_succeeded and refund_failed events"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        # External refund identifier (rfd-*).
        self.id = data.get("id")
        self.amount_refunded = data.get("amount_refunded")
        # amount_refunded minus its share of the charge discount: what the buyer gets back.
        self.amount_refunded_net_discounts = data.get("amount_refunded_net_discounts")
        self.jamm_fee = data.get("jamm_fee")
        self.consumption_tax = data.get("consumption_tax")
        self.original_transaction_fee_waived = data.get(
            "original_transaction_fee_waived"
        )
        # Present only on refund_failed events.
        error = data.get("error")
        self.error = ChargeError(error) if isinstance(error, dict) else error
        # Not present on refund_failed events.
        self.processed_at = data.get("processed_at")

    def __repr__(self):
        return f"RefundInfo(id={self.id}, amount_refunded={self.amount_refunded})"


class WebhookMessage(_RawDataMapping):
    """Represents a parsed webhook message (equivalent to MerchantWebhookMessage)"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.id = data.get("id")
        self.signature = data.get("signature")
        self.created_at = data.get("created_at")
        self.event_type = _coerce_enum(types.EventType, data.get("event_type"))
        self.content = data.get("content", {})  # Will be replaced by parse() method

    def __repr__(self):
        return f"WebhookMessage(id={self.id}, event_type={self.event_type})"


class ChargeMessage(_RawDataMapping):
    """Represents a charge webhook message content (equivalent to ChargeMessage)"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.id = data.get("id")
        self.customer = data.get("customer")
        self.status = _coerce_enum(types.ChargeMessageStatus, data.get("status"))
        self.description = data.get("description")
        self.merchant_name = data.get("merchant_name")
        # Original charge amount, before discount and before any refund.
        self.initial_amount = data.get("initial_amount")
        self.discount = data.get("discount")
        # Final charge amount after discount, before any refund.
        self.final_amount = data.get("final_amount")
        # Total refunded for this charge, once it has been refunded.
        self.amount_refunded = data.get("amount_refunded")
        self.currency = data.get("currency")
        self.processed_at = data.get("processed_at")
        # Jamm fee for this refund event (refund uses the refund fee; cancel uses 0).
        self.jamm_fee = data.get("jamm_fee")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        # "waived" (same-day cancel) or "not_waived" (refund).
        self.original_transaction_jamm_fee = data.get("original_transaction_jamm_fee")
        # Consumption tax (10% of the Jamm fee).
        self.consumption_tax = data.get("consumption_tax")

        # For failed charges.
        error = data.get("error")
        self.error = ChargeError(error) if isinstance(error, dict) else error

        # External refund identifier (rfd-*) on refund / refund_failed webhooks.
        self.refund_id = data.get("refund_id")

        # Refund details on refund / refund_failed webhooks.
        refund = data.get("refund")
        self.refund = RefundInfo(refund) if isinstance(refund, dict) else refund

        # Which API created the charge. This SDK creates charges through
        # off_session_async and on_session, but the field is decoded for every value
        # the wire can carry -- a charge created elsewhere, or before the synchronous
        # off-session API was dropped, still reports its own source.
        self.api_source = _coerce_enum(
            types.ChargeMessageApiSource, data.get("api_source")
        )

        # The merchant's own map from charge creation. Always a dict — the backend
        # omits the key when empty.
        metadata = data.get("metadata")
        self.metadata = metadata if isinstance(metadata, dict) else {}

    def __repr__(self):
        return f"ChargeMessage(id={self.id}, amount={self.final_amount})"


class ContractMessage(_RawDataMapping):
    """Represents a contract webhook message content"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.customer = data.get("customer")
        self.created_at = data.get("created_at")
        self.activated_at = data.get("activated_at")
        self.merchant_name = data.get("merchant_name")

    def __repr__(self):
        return f"ContractMessage(customer={self.customer})"


class UserAccountMessage(_RawDataMapping):
    """Represents a user account webhook message content"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.customer = data.get("customer")
        self.email = data.get("email")
        self.deleted_at = data.get("deleted_at")
        self.merchant_name = data.get("merchant_name")

    def __repr__(self):
        return f"UserAccountMessage(customer={self.customer})"


# Attribute names ChargeMessage reads off the payload, derived from the class so a new
# field cannot fall out of sync with this set.
_CHARGE_FIELDS = frozenset(vars(ChargeMessage({}))) - {"_raw_data"}


# Event types routed to each content class. Names are compared through
# types.event_type_equals, so a numeric wire value routes the same as a string.
_CHARGE_EVENTS = (
    "EVENT_TYPE_CHARGE_CREATED",
    "EVENT_TYPE_CHARGE_UPDATED",
    "EVENT_TYPE_CHARGE_SUCCESS",
    "EVENT_TYPE_CHARGE_FAIL",
    "EVENT_TYPE_REFUND_SUCCEEDED",
    "EVENT_TYPE_REFUND_FAILED",
)
_CONTRACT_EVENTS = ("EVENT_TYPE_CONTRACT_ACTIVATED",)
_USER_ACCOUNT_EVENTS = ("EVENT_TYPE_USER_ACCOUNT_DELETED",)


# ========== Webhook Class ==========


class Webhook:
    """High-level webhook operations and message parsing"""

    def __init__(self, api_client=None):
        # Keep minimal initialization for consistency with other classes
        pass

    @staticmethod
    def parse(webhook_data: Union[Dict[str, Any], str]) -> WebhookMessage:
        """
        Parse command is for parsing the received webhook message.
        It does not call anything remotely, instead returns the suitable object.

        IMPORTANT: this does NOT verify the signature. Prefer
        :meth:`verify_and_parse`, which verifies and parses in one step. If you call
        `parse` directly, always verify first to ensure authenticity.

        Args:
            webhook_data: Webhook message data (dict or JSON string)

        Returns:
            WebhookMessage object with parsed content

        Raises:
            ValueError: If event type is unknown
        """
        if isinstance(webhook_data, str):
            webhook_data = json.loads(webhook_data)

        webhook_data = _to_snake_keys(webhook_data)

        # Create the main webhook message
        out = WebhookMessage(webhook_data)

        content = webhook_data.get("content", {})

        # Route on the coerced event type so a numeric wire value routes the same
        # as the string form.
        event_type = out.event_type

        if any(types.event_type_equals(e, event_type) for e in _CHARGE_EVENTS):
            out.content = ChargeMessage(Webhook._flatten_charge_content(content))
            return out

        if any(types.event_type_equals(e, event_type) for e in _CONTRACT_EVENTS):
            out.content = ContractMessage(content)
            return out

        if any(types.event_type_equals(e, event_type) for e in _USER_ACCOUNT_EVENTS):
            out.content = UserAccountMessage(content)
            return out

        # An event type this release does not know is an error, not a pass-through: the
        # content class it maps to is what gives the payload its shape, and handing back
        # an unrouted message would push that guess onto the caller. Every Jamm SDK
        # raises here (Node, Ruby, PHP, Java), so a new event type means every SDK ships
        # support for it -- relaxing this would have to happen across all of them at
        # once. Unknown *fields* and unknown enum values inside a known event still
        # degrade gracefully; only the routing key is strict.
        raise ValueError("Unknown event type")

    @staticmethod
    def _flatten_charge_content(content: Any) -> Dict[str, Any]:
        """Flatten the nested refund wrapper into a flat ChargeMessage shape.

        Refund webhooks (REFUND_SUCCEEDED / REFUND_FAILED) deliver ``content`` as a
        nested ``{transaction, refund}`` wrapper rather than a flat ChargeMessage.
        Without flattening, every charge field -- including ``id`` -- reads as None.
        The refund's ``rfd-`` id is also surfaced on the flat ``refund_id`` attribute
        the proto documents for refunds.
        """
        if not isinstance(content, dict) or "transaction" not in content:
            return content if isinstance(content, dict) else {}

        transaction = content.get("transaction")
        if not isinstance(transaction, dict):
            return {}

        # Wrapper siblings are carried over so one this release predates stays reachable,
        # but never one that shares a ChargeMessage field name: Go omits every optional
        # field when nil, so a sibling would silently supply charge data the transaction
        # did not send.
        extras = {
            k: v
            for k, v in content.items()
            if k != "transaction" and k not in _CHARGE_FIELDS
        }
        charge = {**extras, **transaction}

        # The wrapper's refund is the refund for this event, whatever the transaction says.
        if "refund" in content:
            charge["refund"] = content["refund"]

        refund = charge.get("refund")
        if isinstance(refund, dict) and refund.get("id") is not None:
            charge["refund_id"] = refund["id"]

        return charge

    @staticmethod
    def verify_and_parse(raw_body: str, client_secret: str) -> WebhookMessage:
        """
        Verify the HMAC signature over the exact received bytes and parse, in one step.

        This is the only entry point that verifies. Go's encoder HTML-escapes ``&`` ``<``
        ``>`` as ``\\u0026`` ``\\u003c`` ``\\u003e`` and emits keys in proto field order, so
        re-serializing the parsed content yields a different digest. This method slices the
        raw ``content`` substring out of ``raw_body`` verbatim and HMACs that.

        Args:
            raw_body: The raw, unmodified webhook request body (str).
            client_secret: Client secret for verification.

        Returns:
            The parsed WebhookMessage.

        Raises:
            ValueError: If raw_body/client_secret is invalid or required fields are missing.
            InvalidSignatureError: If the signature does not match.
        """
        if not raw_body:
            raise ValueError("raw_body cannot be None or empty")
        if client_secret is None:
            raise ValueError("client_secret cannot be None")

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        signature = parsed.get("signature") if isinstance(parsed, dict) else None
        if not signature:
            raise ValueError("Webhook body is missing the 'signature' field")

        raw_content = Webhook._extract_raw_content(raw_body)
        digest = hmac.new(
            client_secret.encode("utf-8"), raw_content.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        expected = f"sha256={digest}"

        if not Webhook.secure_compare(expected, signature):
            raise InvalidSignatureError("Digests do not match")

        return Webhook.parse(parsed)

    @staticmethod
    def _extract_raw_content(raw_body: str) -> str:
        """
        Extract the top-level ``content`` value substring from a raw webhook body verbatim,
        without decoding or re-serializing it, so the exact signed bytes are recovered.
        """
        decoder = json.JSONDecoder()
        n = len(raw_body)
        i = 0
        while i < n and raw_body[i].isspace():
            i += 1
        if i >= n or raw_body[i] != "{":
            raise ValueError("Webhook body must be a JSON object")
        i += 1  # consume '{'

        # Scan every top-level key. Duplicate keys are rejected: json.loads keeps the LAST
        # occurrence while this returns the FIRST, so a duplicate `content` could otherwise
        # verify one payload and parse another (signature bypass).
        seen = set()
        content = None
        while True:
            while i < n and (raw_body[i].isspace() or raw_body[i] == ","):
                i += 1
            if i < n and raw_body[i] == "}":
                break
            if i >= n or raw_body[i] != '"':
                raise ValueError("Malformed webhook JSON")
            key, i = decoder.raw_decode(raw_body, i)  # parse the key string
            if key in seen:
                raise ValueError(f"Duplicate top-level key in webhook body: {key}")
            seen.add(key)
            while i < n and raw_body[i].isspace():
                i += 1
            if i >= n or raw_body[i] != ":":
                raise ValueError("Malformed webhook JSON")
            i += 1  # consume ':'
            while i < n and raw_body[i].isspace():
                i += 1
            value_start = i
            _, i = decoder.raw_decode(raw_body, i)  # parse the value; i = index past it
            if key == "content":
                content = raw_body[value_start:i]

        if content is None:
            raise ValueError("Webhook body does not contain 'content' field")
        return content

    @staticmethod
    def secure_compare(a: str, b: str) -> bool:
        """
        Securely compare two strings of equal length.
        This method is a port of ActiveSupport::SecurityUtils.secure_compare
        which works on non-Rails platforms.

        Args:
            a: First string
            b: Second string

        Returns:
            True if strings are equal, False otherwise
        """
        if len(a) != len(b):
            return False

        # Convert strings to bytes
        a_bytes = a.encode("utf-8")
        b_bytes = b.encode("utf-8")
        result = 0

        # XOR each byte and accumulate the result
        for x, y in zip(a_bytes, b_bytes):
            result |= x ^ y

        return result == 0


# Make sure all classes are available at module level
__all__ = [
    "Webhook",
    "WebhookMessage",
    "ChargeMessage",
    "ChargeError",
    "ContractMessage",
    "RefundInfo",
    "UserAccountMessage",
    "InvalidSignatureError",
]
