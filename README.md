# Jamm SDK for Python

Lightweight Python client for the Jamm API. Focused on:

- Straightforward auth (client credentials OAuth2)
- Clean dict responses (flattened where practical)
- Helpful error metadata (`error_type`, `error_code`, decoded debug values)
- Simple pagination (lazy charge iterator)

## Installation

From PyPI:

```bash
pip install jamm
```

Local development (editable):

```bash
pip install -e .
```

## Quick Start

```python
import jamm

client = jamm.configure(
    client_id="your_client_id",
    client_secret="your_client_secret",
    env="staging",  # the sandbox; use "production" for live money
)

print(client.healthcheck())
```

## Configuration

The SDK can be configured using environment variables or programmatically:

### Environment Variables

`ClientConfig()` reads these when the matching argument is omitted:

| Variable | Setting |
| --- | --- |
| `JAMM_CLIENT_ID` | `client_id` |
| `JAMM_CLIENT_SECRET` | `client_secret` |
| `JAMM_ENVIRONMENT` | `environment` (default `production`) |
| `JAMM_PLATFORM` | `platform`: `1`, `true` or `yes` turns it on. `jamm.configure` also uses it when `platform` is omitted. |

### Programmatic Configuration

```python
from jamm import JammClient, ClientConfig

config = ClientConfig(
    client_id="your_client_id",
    client_secret="your_client_secret",
    environment="staging",
)

client = JammClient(config)
```

`environment` selects the hosts. Sandbox and live use separate credentials, so change
`client_id` and `client_secret` with it (webhook signatures are checked with `client_secret` too):

| `environment` | API host | Who it is for |
| --- | --- | --- |
| `staging` | `api.staging.jamm-pay.jp` | The sandbox. Staging credentials are issued alongside production ones. |
| `production` (default) | `api.jamm-pay.jp` | Live money. |

`client_secret` is held as a pydantic `SecretStr`, so printing or logging the config —
or a traceback that captures it — shows `**********` rather than the credential. Read
the value back with `config.client_secret.get_secret_value()`.

## API version

Every request to the Jamm API carries a `Jamm-API-Version` header. It defaults to
the dated API version this SDK was built against, exposed as
`jamm.apiversion.API_VERSION`. To stay on the version you integrated against, pass `api_version` to
`jamm.configure`:

```python
client = jamm.configure(
    client_id="your_client_id",
    client_secret="your_client_secret",
    env="production",
    api_version="2026-08-26",
)
```

An empty `api_version` means the built-in version. Any other malformed date, or one newer than it, raises `ValueError`
at configure time; upgrade the SDK to use a newer API version.
The API rejects a version it no longer serves; the error lists the versions it does. Responses to a pinned older version follow that version's shape, so fields added since come back empty in this SDK's types.

Every versioned response echoes what served it in two headers:
`Jamm-API-Version` is the version, and `Jamm-API-Version-Source` is how it was
chosen: `header` (the version this SDK sent), `pin` (your account's pinned
version), `default` (no header, and no pin we could read), or `forced` (Jamm
temporarily served its newest shape, which no dated version describes, so
`Jamm-API-Version` is omitted). A request rejected before a version is chosen
carries neither.

OAuth2 token requests are excluded: they go to the identity service, which is
not versioned.


## Features Overview

| Domain      | Highlights                                                                    |
| ----------- | ----------------------------------------------------------------------------- |
| Healthcheck | Ping connectivity quickly                                                     |
| Customers   | CRUD + contract; normalized: `linkInitialized`, `bankInformation`, `status`     |
| Payments    | On-session / off-session async flows                                          |
| Refunds     | Full, partial, and cancel-only refunds                                        |
| Contracts   | Fetch existing customer contract                                              |
| Charges     | Get, list, lazy iterator `charges.iter()`                                     |
| Banking     | Bank search, branches (get/search/list)                                       |
| Webhooks    | Verify + parse in one step; typed content per event                            |
| Platform    | Call the API on behalf of a merchant                                          |
| Types       | Enum constants and comparison helpers                                         |
| Errors      | Unified `ApiError` with rich metadata                                         |

## API Reference

### Health Check

```python
# Verify API connectivity -- returns the parsed response body, raises ApiError if down
response = client.healthcheck()
print(response)

# Or as a boolean, for a readiness probe
client.health.check()
```

### Customer Management

```python
buyer_data = {
    "email": "customer@example.com",
    "name": "John Doe",
    "katakana_last_name": "ドウ",
    "katakana_first_name": "ジョン",
    "address": "123 Tokyo Street, Shibuya",
    "birth_date": "1990-01-01",
    "gender": "male",
    "force_kyc": False,
    "metadata": {"source": "api"}
}

customer = client.customers.create(buyer=buyer_data)
print(customer["id"])  # flattened
customer = client.customers.get("cus-customer_id_here")
updated = client.customers.update(
    customer_id="cus-customer_id_here",
    # metadata values are strings, and the map replaces the customer's existing metadata.
    data={"name": "Updated Name", "metadata": {"updated": "true"}},
)
contract = client.customers.get_contract("cus-customer_id_here")
delete_result = client.customers.delete("cus-customer_id_here")
```

### Payment Processing

```python
from datetime import datetime, timedelta, timezone
# Build the timestamp in UTC. datetime.now() returns local time, so suffixing it with
# "Z" would mislabel it and shift the expiry by your machine's offset.
expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
    "%Y-%m-%dT%H:%M:%SZ"
)

# Off-session charges are asynchronous: this returns immediately with a charge ID and
# the charge settles in the background. Poll client.charges.get(charge_id) for the
# outcome, or wait for the webhook. idempotency_key is auto-filled with a fresh UUID
# when omitted, which is not the same as a safe retry: re-calling after a lost response
# generates a different key and charges twice. Pass your own key and reuse it to retry.
off_session = client.payments.off_session_async(
    customer_id="cus-customer_id_here",
    price=1000,
    description="Monthly subscription",
    expires_at=expires_at,
    idempotency_key="order-2026-001",  # optional
)

on_session = client.payments.on_session(
    customer_id="cus-customer_id_here",
    price=1000,
    description="One-time payment",
    redirect_urls={
        "success_url": "https://example.com/success",
        "failure_url": "https://example.com/cancel",
    },
    expires_at=expires_at,
)

# on_session adds expires_at to the buyer dict it is given, so pass a copy.
new_customer_session = client.payments.on_session(
    buyer=dict(buyer_data),
    redirect_urls={
        "success_url": "https://example.com/success",
        "failure_url": "https://example.com/cancel",
    },
    expires_at=expires_at,
)

new_customer_with_charge = client.payments.on_session(
    buyer=dict(buyer_data),
    price=1000,
    description="Initial payment",
    redirect_urls={
        "success_url": "https://example.com/success",
        "failure_url": "https://example.com/cancel",
    },
    expires_at=expires_at,
)
```

`on_session` does not raise for business failures such as an unknown or inactive
customer. It returns `success` false with an `error`, so check it before using the
response:

```python
if not on_session.get("success"):
    error = on_session.get("error") or {}
    if jamm.types.on_session_payment_error_code_equals(
        jamm.types.OnSessionPaymentErrorCode.ON_SESSION_PAYMENT_ERROR_CODE_CUSTOMER_NOT_FOUND,
        error.get("code"),
    ):
        ...
```

### Contract Management

```python
contract = client.contracts.get("cus-customer_id_here")
if contract:
    print("Contract found")
else:
    print("No active contract")
```

### Charge Operations

```python
# Returns None when the charge does not exist (404).
# A rejected request (400) or an authorization failure (403) still raises ApiError.
charge = client.charges.get("trx-charge_id_here")
page = client.charges.list(customer_id="cus-customer_id_here", page_size=25)
for c in client.charges.iter(customer_id="cus-customer_id_here", page_size=100, limit=500):
    process(c)
```

### Refunds

A refund is always processed asynchronously. A successful response means the request was
accepted; the outcome arrives by webhook (`refund_succeeded` or `refund_failed`). A full
refund within the same-day cancellation window cancels the charge directly. A partial refund
(an `amount` below the charge amount), or a full one after that window, creates a bank
transfer refund. `cancel_only=True` always cancels the whole charge, so don't combine it with
`amount`. Charges older than 180 days can't be refunded.

```python
# Full refund
result = client.payments.refund("trx-charge_id_here")
print(result["chargeId"], result["refundId"])

# Partial refund, in JPY
client.payments.refund("trx-charge_id_here", amount=500)

# Cancel only -- do not fall back to a bank transfer refund
client.payments.refund("trx-charge_id_here", cancel_only=True)
```

### Platform Mode

Platform credentials can call the API on behalf of a merchant. Configure with
`platform=True`, then pass `merchant` to any merchant-scoped operation. Bank and branch
lookups need merchant credentials and are not available in platform mode.

```python
client = jamm.configure(
    env="staging",
    client_id="your_platform_client_id",
    client_secret="your_platform_client_secret",
    platform=True,
)

client.healthcheck()  # connectivity only; it does not check access to a merchant
client.customers.create(buyer_data, merchant="mer-merchant_id_here")
client.payments.off_session_async(
    "cus-customer_id_here",
    1000,
    description="Monthly subscription",
    idempotency_key="order-2026-001",
    merchant="mer-merchant_id_here",
)
client.payments.refund("trx-charge_id_here", merchant="mer-merchant_id_here")
```

Platform mode authenticates against a separate identity service, so it requires platform
credentials — merchant credentials will not work. Passing `merchant` in merchant mode
(`platform=False`, or `platform` omitted with `JAMM_PLATFORM` unset), or with a malformed
merchant ID, raises `ValueError` before any request is sent.

### Enum Constants

Enums arrive as strings over REST. Webhooks send `event_type` as a string, but enums inside
`content` (such as `status` and `api_source`) as integers. `jamm.types` carries the
constants and comparison helpers that bridge the two, so you never hand-write the wire
strings:

```python
import jamm

if jamm.types.error_type_equals(
    jamm.types.ErrorType.ERROR_TYPE_KYC_REJECTED, error.error_type
):
    ...

if jamm.types.api_source_equals(
    jamm.types.ChargeMessageApiSource.API_SOURCE_ON_SESSION, charge.api_source
):
    ...
```

Available: `ErrorType`, `EventType`, `ChargeMessageStatus`, `ChargeMessageApiSource`,
`KycStatus`, `PaymentAuthorizationStatus`, `ContractStatus`, `DepositType`,
`OnSessionPaymentErrorCode`, each with a matching `*_equals` helper.

Either side may be an enum constant or its full wire name. Prefix-stripped short names
(`"AUTHORIZED"`) are not accepted — no suffix rule can distinguish a constant from a
sibling that ends with it, and `AUTHORIZED` matching `NOT_AUTHORIZED` would invert an
authorization check. A value the SDK does not recognize matches no constant.

### Webhooks

`verify_and_parse` is the only entry point that verifies: it checks the HMAC signature
over the exact received bytes and parses in one step.

`Webhook.parse` is still public and does **not** verify. It parses unverified payloads
for known event types — it still raises on invalid JSON and on an event type it does not
recognise, but it checks no signature. Never use its output for a trust decision; reach
for it only when you have already verified the bytes yourself.

```python
# raw_request_body is the body exactly as received, as bytes (Flask: request.get_data()).
try:
    message = jamm.Webhook.verify_and_parse(raw_request_body.decode("utf-8"), client_secret)
except jamm.InvalidSignatureError:
    ...  # not from Jamm: reject it and stop
except ValueError:
    # Malformed, or an event with no content type in this SDK, such as the
    # dashboard's test event (EVENT_TYPE_TESTING): acknowledge it and stop.
    ...

if jamm.types.event_type_equals(
    jamm.types.EventType.EVENT_TYPE_REFUND_SUCCEEDED, message.event_type
):
    charge = message.content
    print(charge.id, charge.status, charge.refund_id)
    print(charge.refund.amount_refunded, charge.refund.jamm_fee)

    # Your own map from charge creation. Always a dict; `{}` when there is none.
    for key, value in charge.metadata.items():
        print(key, value)
```

Content is typed per event: `ChargeMessage` for charge and refund events,
`ContractMessage` for `CONTRACT_ACTIVATED`, and `UserAccountMessage` for
`USER_ACCOUNT_DELETED`. Refund events arrive as a nested `{transaction, refund}` wrapper
and are flattened onto `ChargeMessage`, with the refund's `rfd-` id on `refund_id` and
the details on `refund`.

Fields the backend adds later are never fatal, and do not need an SDK release to be
readable: every content class is a read-only mapping over its payload.

```python
charge["a_field_this_release_predates"]   # -> its value; KeyError if absent
charge.get("maybe_missing")               # -> None if absent
dict(charge)                              # the content mapping (flattened, for refunds)
```

For refund events that mapping is the flattened charge, not the `{transaction, refund}`
wrapper the backend sent.

Attribute access stays strict: `charge.typo` raises `AttributeError` rather than
returning `None`. Top-level mutation is refused — `charge["x"] = 1` and `del charge["x"]`
raise `TypeError`, `charge.update(...)` raises `AttributeError`.

That guarantee stops at the top level. Nested values that came from the payload are
shared, not copied — `dict(charge)` is shallow — so `charge.metadata["k"] = v` succeeds
and every other reader of that payload sees it. When the charge carried no metadata,
`charge.metadata` is a fresh `{}` and writes stay local, so a metadata-less charge will
not show you the difference. Use `copy.deepcopy(dict(charge))` to edit nested values.

### Banking Operations

```python
bank = client.banks.get("0001")
search_results = client.banks.search("みずほ")
branch = client.bank_branches.get("0001", "001")
branches = client.bank_branches.search("0001", "東京")
all_branches = client.bank_branches.list_for_bank("0001")
```

## Authentication

OAuth2 client credentials handled automatically once configured.

## Development Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Running Tests

The unit and end-to-end suites are not published with the SDK. They run in Jamm's CI on every change.

## Helper: generate_buyer()

```python
from faker import Faker
import time

def generate_buyer(base_email=None, name=None, force_kyc=False):
    """Generate realistic buyer data for testing"""
    fake_en = Faker("en_US")
    fake_jp = Faker("ja_JP")
    timestamp = int(time.time())

    return {
        "email": f"{fake_en.user_name()}+{timestamp}@example.com",
        "name": name or fake_en.name(),
        "katakana_last_name": fake_jp.last_kana_name(),
        "katakana_first_name": fake_jp.first_kana_name(),
        "address": fake_jp.address(),
        "birth_date": fake_en.date_of_birth(minimum_age=20, maximum_age=70).strftime("%Y-%m-%d"),
        "gender": fake_en.random_element(["male", "female"]),
        "force_kyc": force_kyc,
        "metadata": {"source": "faker_generated", "timestamp": str(timestamp)}
    }

# Usage
buyer_data = generate_buyer()
customer = client.customers.create(buyer=buyer_data)
```

## Error Handling

A failed API call raises `jamm.ApiError`, except `payments.on_session`, which reports business
failures in its response (see Payment Processing). Lookups such as `charges.get` and `contracts.get` return
`None` on a 404 instead, and invalid arguments raise `ValueError` or `TypeError` before any request is sent.

| Field            | Meaning                                                            |
| ---------------- | ------------------------------------------------------------------ |
| `code`           | HTTP status (0 = network/transport)                                |
| `message`        | Short description                                                  |
| `details`        | Parsed JSON body                                                   |
| `error_type`     | Internal debug enum-like (e.g. `ERROR_TYPE_PAYMENT_CHARGE_FAILED`) |
| `error_code`     | String code when the error body carries one, otherwise `None`      |
| `debug_values`   | All collected debug markers                                        |
| `decoded_values` | Base64-decoded detail values                                       |

```python
from jamm import ApiError
try:
    client.payments.refund("trx-nonexistent")
except ApiError as e:
    print(e.code, e.message, e.error_type)
    if getattr(e, "error_code", None):
        print("error_code:", e.error_code)
    if getattr(e, "decoded_values", None):
        print("decoded:", e.decoded_values)
```

Network issues surface with `code == 0`, and `details["exception_type"]` names the exception (e.g. `ConnectionError`).
When the OAuth token request itself fails (for example, wrong credentials), the error carries only
`code`, `message` and `details`, and `code` can be `None`.

## Feedback

To report a bug or ask for a feature, open an issue on
[jamm-pay/python-sdk](https://github.com/jamm-pay/python-sdk/issues). The repository is published from Jamm's
internal source on each release, so pull requests there can't be merged.
