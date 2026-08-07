# Jamm SDK for Python

Lightweight Python client for the Jamm API. Focused on:

- Straightforward auth (client credentials OAuth2)
- Clean dict responses (flattened where practical)
- Helpful error metadata (`error_type`, `error_code`, decoded debug values)
- Simple pagination (lazy charge iterator)

## Installation

Production (when published):

```bash
pip install jamm-sdk
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

`environment` selects the hosts, so it is the only setting needed to move between
sandbox and live:

| `environment` | API host | Who it is for |
| --- | --- | --- |
| `staging` | `api.staging.jamm-pay.jp` | The sandbox. Staging credentials are issued alongside production ones. |
| `production` (default) | `api.jamm-pay.jp` | Live money. |

`client_secret` is held as a pydantic `SecretStr`, so printing or logging the config —
or a traceback that captures it — shows `**********` rather than the credential. Read
the value back with `config.client_secret.get_secret_value()`.

## Features Overview

| Domain      | Highlights                                                                    |
| ----------- | ----------------------------------------------------------------------------- |
| Healthcheck | Ping connectivity quickly                                                     |
| Customers   | CRUD + contract; normalized: `link_initialized`, `bank_information`, `status` |
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
    data={"name": "Updated Name", "metadata": {"updated": True}},
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
        "success_url": "https://yoursite.com/success",
        "failure_url": "https://yoursite.com/cancel",
    },
    expires_at=expires_at,
)

new_customer_session = client.payments.on_session(
    buyer=buyer_data,
    redirect_urls={
        "success_url": "https://yoursite.com/success",
        "failure_url": "https://yoursite.com/cancel",
    },
    expires_at=expires_at,
)

new_customer_with_charge = client.payments.on_session(
    buyer=buyer_data,
    price=1000,
    description="Initial payment",
    redirect_urls={
        "success_url": "https://yoursite.com/success",
        "failure_url": "https://yoursite.com/cancel",
    },
    expires_at=expires_at,
)
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
accepted; the outcome arrives by webhook (`refund_succeeded` or `refund_failed`). If the
same-day cancellation window has not passed the charge is cancelled directly, otherwise a
bank transfer refund is created.

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
`platform=True`, then pass `merchant` to any operation:

```python
client = jamm.configure(
    env="develop",
    client_id="your_platform_client_id",
    client_secret="your_platform_client_secret",
    platform=True,
)

client.healthcheck(merchant="mer-merchant_id_here")
client.customers.create(buyer_data, merchant="mer-merchant_id_here")
client.payments.off_session_async("cus-customer_id_here", 1000, merchant="mer-merchant_id_here")
client.payments.refund("trx-charge_id_here", merchant="mer-merchant_id_here")
```

Platform mode authenticates against a separate identity service, so it requires platform
credentials — merchant credentials will not work. Passing `merchant` without
`platform=True`, or with a malformed merchant ID, raises `ValueError` before any request
is sent.

### Enum Constants

Enums arrive as strings over REST and as integers on webhooks. `jamm.types` carries the
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

`verify_and_parse` is the recommended entry point: it verifies the HMAC signature over
the exact received bytes and parses in one step, so verification cannot be skipped.

```python
message = jamm.Webhook.verify_and_parse(raw_request_body, client_secret)

if jamm.types.event_type_equals(
    jamm.types.EventType.EVENT_TYPE_REFUND_SUCCEEDED, message.event_type
):
    charge = message.content
    print(charge.id, charge.status, charge.refund_id)
    print(charge.refund.amount_refunded, charge.refund.jamm_fee)
```

Content is typed per event: `ChargeMessage` for charge and refund events,
`ContractMessage` for `CONTRACT_ACTIVATED`, and `UserAccountMessage` for
`USER_ACCOUNT_DELETED`. Refund events arrive as a nested `{transaction, refund}` wrapper
and are flattened onto `ChargeMessage`, with the refund's `rfd-` id on `refund_id` and
the details on `refund`. Fields the backend adds in future are ignored rather than
fatal, and remain reachable on `_raw_data`.

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

Unit tests (no credentials, no network):

```bash
python -m pytest tests
```

End-to-end tests against a live environment:

```bash
export MERCHANT_CLIENT_ID=your_client_id
export MERCHANT_CLIENT_SECRET=your_client_secret
python test.e2e/run_tests.py
```

There is also a manual walkthrough that exercises every service and prints a report:

```bash
export MERCHANT_CLIENT_SECRET=your_client_secret
python test.e2e/manual_smoke.py --client-id YOUR_ID --env staging
```

Abbreviated example output:

```text
✅ Healthcheck ok
✅ Customer created
✅ Off-session payment created
✅ On-session payment created
```

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
        "email": f"{fake_en.user_name()}+{timestamp}@jamm-pay.jp",
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

Every failed SDK call raises `jamm.ApiError`.

| Field            | Meaning                                                            |
| ---------------- | ------------------------------------------------------------------ |
| `code`           | HTTP status (0 = network/transport)                                |
| `message`        | Short description                                                  |
| `details`        | Parsed JSON body                                                   |
| `error_type`     | Internal debug enum-like (e.g. `ERROR_TYPE_PAYMENT_CHARGE_FAILED`) |
| `error_code`     | High-level code (`internal`, `invalid`, etc.)                      |
| `debug_values`   | All collected debug markers                                        |
| `decoded_values` | Base64-decoded detail values                                       |

```python
from jamm import ApiError
try:
    client.charges.get("trx-nonexistent")
except ApiError as e:
    print(e.code, e.message, e.error_type)
    if e.error_code:
        print("error_code:", e.error_code)
    if e.decoded_values:
        print("decoded:", e.decoded_values)
```

Network issues surface with `code == 0` and `details` containing `{"network_error": True}`.

## Notes & Next Steps

Planned (non-breaking): enum wrapper for `error_type`, helper predicates, optional typed response models. Contributions welcome.
