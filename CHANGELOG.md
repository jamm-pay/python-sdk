# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2026-10-21

### Security

- The SDK now requires `certifi` 2026.10.19 or later, whose trusted root bundle is updated after the private keys of eight eMudhra intermediate CA certificates were compromised. If you pin `certifi`, raise the pin to 2026.10.19 or later.

## [0.9.0] - 2026-10-05

### Added

- Every request to the Jamm API (not OAuth token requests) sends a `Jamm-API-Version` header defaulting to the API version this SDK was built for (`jamm.apiversion.API_VERSION`). To stay on an older version, pass `api_version` to `jamm.configure`; a newer one needs an SDK upgrade.
- New error type `ERROR_TYPE_PAYMENT_CHARGE_OVER_DAILY_LIMIT`: the charge would exceed the daily limit of the buyer's bank account. Retry after midnight JST.
- Charge webhooks expose `metadata`, the map you set when creating the charge, on every charge and refund event. It is `{}` when the charge has none.
- Webhook messages can be read like a dict, so a field newer than your SDK is available as `charge["new_field"]`.

### Changed

- The SDK version header is renamed from `X-SDK-Version` to `Jamm-SDK-Version`. If a proxy or firewall allowlists outgoing headers, add `Jamm-SDK-Version`.
- Webhook parsing accepts both `snake_case` and `camelCase` field names, so a future change to the webhook format won't break it.
- Webhook message classes are now mappings: an empty payload is falsy, `==` compares content, and they are no longer hashable.

### Deprecated

- `ERROR_TYPE_CSV_DUPLICATE_USER` is no longer returned.

### Removed

- **Breaking:** `Webhook.verify` is removed. It rejected every real webhook. Use `Webhook.verify_and_parse(raw_body, client_secret)`. Code that calls `verify` inside `except InvalidSignatureError` now gets an `AttributeError` instead, so replace those calls before upgrading.

## [0.8.0] - 2026-08-05

### Added

- Refund support: `Payment.refund(charge_id, amount=None, cancel_only=None)` for full, partial and cancel-only refunds. The refund is processed asynchronously and the outcome arrives by webhook (`refund_succeeded` / `refund_failed`).
- Platform mode: configure with `platform=True` to authenticate against the platform identity service, then pass `merchant="mer-..."` to any operation to act on its behalf. A `merchant` used outside platform mode, or a malformed merchant ID, raises `ValueError` before any request is sent.
- `jamm.types` — enum constants (`ErrorType`, `EventType`, `ChargeMessageStatus`, `ChargeMessageApiSource`, `KycStatus`, `PaymentAuthorizationStatus`, `ContractStatus`, `DepositType`, `OnSessionPaymentErrorCode`) with `*_equals` helpers that compare an int enum value against the string form the wire carries. Names must match in full: prefix-stripped short names are not accepted, because no suffix rule can tell a constant apart from a sibling ending with the same word (`"AUTHORIZED"` would otherwise match `PAYMENT_AUTHORIZATION_STATUS_NOT_AUTHORIZED`).
- `Payment.get` and `Payment.list` for charge lookups, alongside the existing `Charge` wrapper.
- `Webhook.parse` now handles `EVENT_TYPE_USER_ACCOUNT_DELETED`, returning the new `UserAccountMessage` (it previously raised `ValueError: Unknown event type`).
- `ChargeMessage` now exposes `status`, `api_source`, `amount_refunded`, `jamm_fee`, `consumption_tax`, `original_transaction_jamm_fee`, `refund_id` and `refund`, and decodes `error` and `refund.error` into typed objects (`ChargeError`, `RefundInfo`). Both implement the read-only mapping protocol, so every *read* that worked on the raw dicts they replaced still works — `error["code"]`, `error.get("code")`, `"code" in error`, `for key in error`, `error.items()`, `len(error)`, `dict(error)` and `==` against a plain dict. Mutation does not: `error["code"] = x` and `del error["code"]` now raise `TypeError`, and `error.update(...)` raises `AttributeError`, where the raw dict accepted all three. Build a copy with `dict(error)` if you need to write.

### Fixed

- Refund webhooks (`refund_succeeded` / `refund_failed`) deliver `content` as a nested `{transaction, refund}` wrapper. `Webhook.parse` now flattens it, so every charge field — `id` included — reads correctly instead of `None`, and the refund's `rfd-` id is surfaced on `refund_id`.
- Numeric enum wire values now resolve onto their string constant, so webhook payloads (serialized by Go's `json.Marshal`) read the same as REST responses. A value the SDK does not recognize is passed through verbatim rather than rewritten to the enum's zero constant, so a future event or status stays distinguishable from a genuinely unspecified one when diagnosing a dropped webhook.
- `jamm.ping()` works. It called `Healthcheck.ping()` on the class and raised `TypeError: ping() missing 1 required positional argument`, so the documented convenience entry point had never been callable.
- The `JAMM_PLATFORM` environment variable takes effect. `configure()` defaulted its `platform` argument to `False`, which always overwrote the value read from the environment, so the variable `ClientConfig` advertises did nothing. It now defaults to "not specified"; passing a literal `False` still forces merchant mode.
- `Healthcheck.check()` raises `ValueError` for a malformed or non-platform `merchant` instead of returning `False`. A local argument error is the caller's bug, and reporting it as an unhealthy service sent operators looking for an outage.
- Send the `X-SDK-Version` header on every service call. It was only set on the legacy HTTP client, which served just `client.healthcheck()`, so no other request carried it despite 0.5.0 announcing the header.
- The reported SDK version no longer drifts: it is read from installed package metadata, falling back to `pyproject.toml`. The previous hardcoded fallback was two releases behind and was reported to the backend on every request.
- `importing jamm` no longer prints "API import hook installed" to stdout, which corrupted host programs whose stdout is data.

### Removed

- **Breaking:** removed the synchronous off-session payment. `Payment.off_session` and the underlying `POST /v1/payments/off-session` call are gone, along with the `OffSessionPaymentRequest` / `OffSessionPaymentResponse` model re-exports. Use `Payment.off_session_async`, which returns immediately with a charge ID and settles in the background — poll `Charge.get(charge_id)` or wait for the charge webhook. It also auto-fills `idempotency_key` so the request always carries one, which the synchronous call could not offer — but the auto-filled UUID is regenerated per call, so retrying after a lost response needs a key you supply and reuse yourself.

  Nothing in the SDK can create or send a synchronous off-session charge anymore. Two things related to it necessarily remain, both read-only:

  - `ChargeMessage.api_source` still decodes `API_SOURCE_OFF_SESSION_SYNC`, and `jamm.types` still exposes the constant. The backend keeps emitting it for charges created before this release, so dropping it would make those webhooks unreadable.
  - `lib/proto/` still contains the generated `OffSessionPayment` stub and its request/response messages. That directory mirrors the shared `api/v1/payment.proto`, which still declares the RPC because other Jamm SDKs continue to offer it; it is not reachable through any Python SDK method.

### Changed

- `Customer.get`, `Charge.get`, `Payment.get`, `Customer.get_contract` and `Contract.get` return `None` instead of raising when the record is absent, so `if result is None` is a uniform check across every lookup. Only HTTP 404 maps to `None`. A rejected request (400) and an authorization failure (403) both still raise: the REST gateway returns 400 for a malformed request or validation failure, and the platform middleware returns 403 for "platform is not authorized to act on behalf of this merchant" — reporting either as "no such record" would hide a caller bug or a misconfigured platform scope.
- `Contract.get` now delegates to `Customer.get_contract` rather than duplicating it, so the two cannot drift apart.
- **Breaking:** `ClientConfig.client_secret` is a pydantic `SecretStr` rather than a `str`. A config object reaches `print()`, a logger, a `ValidationError` and every traceback frame that holds it, and each of those renders the model's repr — which printed the live credential. It now renders as `**********`. `jamm.configure(...)` and assignment still take a plain string, so only *reading* the attribute changes: use `config.client_secret.get_secret_value()`. Nothing else in the SDK is affected — `Webhook.verify` and `Webhook.verify_and_parse` take the secret as their own `str` argument.
- **Breaking:** `client.healthcheck()` (and `client.ping()`) return the parsed response body, not a raw `requests.Response`. They were the last calls on the legacy HTTP client — a second healthcheck implementation alongside the `Healthcheck` service `jamm.ping()` uses, and the only path skipping the retry and interceptor plumbing. Both now delegate to that service, also reachable as `client.health`. Callers reading `response.status_code` or `response.text` should read the returned dict instead, and a non-2xx response now raises `ApiError` (with the retries and the unified error shape) rather than `requests.HTTPError`.

## [0.7.0] - 2026-07-14

### Changed

- `expires_at` on off-session and contract requests now accepts up to 31 days ahead (was 30 days).

## [0.6.0] - 2026-07-03

### Added

- Added `Webhook.verify_and_parse(raw_body, client_secret)` — verifies the HMAC signature over the exact received `content` bytes and parses in one step. Unlike `Webhook.verify`, it is not broken by JSON re-serialization (correctly handles `&`, `<`, `>` in content) and rejects bodies with duplicate top-level keys.

## [0.5.0] - 2026-07-01

### Added

- Send the `X-SDK-Version` request header (`python:<version>`) so the backend can track SDK version usage per merchant

## [0.4.0] - 2026-05-20

### Added

- Added `Payment.off_session_async` for async off-session charges
- Auto-fill `idempotency_key` with `uuid.uuid4()` when `None`, empty, or whitespace
- Raise `TypeError` for non-string non-`None` `idempotency_key` values

## [0.3.0] - 2025-11-11

### Added

- Enriched `ApiError` with `error_type`, `error_code`, and decoded debug values

### Removed

- Deprecated legacy contract / charge wrapper APIs

## [0.2.0] - 2025-11-11

### Changed

- Version bump aligned with other SDKs

## [0.1.0] - 2025-06-26

### Added

- Initial API client and service wrappers (Customer, Payment, Webhooks)
