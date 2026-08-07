import uuid
from typing import Dict, Any, Optional
from .api.payment_api import PaymentApi
from .api.client import ApiClient, ApiError as ClientApiError
from .errors import ApiError, NOT_FOUND_CODES


class Payment:
    """High-level payment operations"""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api = PaymentApi(api_client)

    def _merchant_headers(self, merchant: Optional[str]) -> Dict[str, str]:
        return self.api.api_client.merchant_headers(merchant)

    def on_session(
        self,
        customer_id: Optional[str] = None,
        price: Optional[int] = None,
        description: Optional[str] = None,
        expires_at: Optional[str] = None,
        redirect_urls: Optional[Dict[str, str]] = None,
        buyer: Optional[Dict[str, Any]] = None,
        merchant: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process an on-session payment (customer present)

        Args:
            customer_id: Customer ID (optional)
            price: Payment amount (optional)
            description: Description of the charge
            expires_at: ISO-8601 format expiration date (e.g. "2025-06-01T00:00:00Z")
            redirect_urls: Dict containing success_url and failure_url
            buyer: Customer information (email, phone, name, etc.)
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")
            **kwargs: Additional parameters

        Returns:
            Payment result

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If payment processing fails
        """
        headers = self._merchant_headers(merchant)

        try:
            # Build the base request
            request_body = {}

            # Add customer ID if provided
            if customer_id is not None:
                request_body["customer"] = customer_id

            # Create charge object only if price is provided
            if price is not None:
                charge = {"price": price}
                if description:
                    charge["description"] = description

                # Add expires_at to charge object if provided
                if expires_at:
                    charge["expires_at"] = expires_at

                request_body["charge"] = charge

            # Handle buyer information
            buyer_dict = buyer or {}  # Use provided buyer or create empty dict

            # If no charge object (no price) and expires_at is provided, add expires_at to buyer
            if price is None and expires_at is not None:
                buyer_dict["expires_at"] = expires_at

            # Add buyer to request if it's not empty
            if buyer_dict:
                request_body["buyer"] = buyer_dict

            # Add redirect URLs if provided
            if redirect_urls:
                request_body["redirect"] = redirect_urls

            # Add any additional parameters
            for key, value in kwargs.items():
                if key not in request_body:
                    request_body[key] = value

            return self.api.on_session_payment(request_body, header_params=headers)
        except ClientApiError as e:
            # Preserve enriched ApiError from low-level client (includes error_type, details)
            raise e
        except Exception as e:
            raise ApiError.from_error(e)

    def off_session_async(
        self,
        customer_id: str,
        price: int,
        description: Optional[str] = None,
        expires_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        merchant: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process an asynchronous off-session payment.

        Returns immediately with a charge ID; the charge is settled in the
        background. Use the returned charge ID to poll for the final result.

        Auto-fills ``idempotency_key`` with a fresh UUID when the caller does
        not supply one, so the request always carries a key. That is not the
        same as being retry-safe: the auto-filled key is regenerated on every
        call, so retrying after a lost response would send a different key and
        charge the customer twice. To retry safely, supply your own key and
        reuse the same value -- a caller-supplied key is left untouched.
        Matches the Java/Ruby/Node/PHP SDKs: ``None``, empty, and
        whitespace-only strings all auto-fill.

        Args:
            customer_id: Customer ID
            price: Charge amount
            description: Description of the charge
            expires_at: ISO-8601 format expiration date (e.g. "2025-06-01T00:00:00Z")
            idempotency_key: Retry-safety key. Auto-filled with a fresh UUID
                when blank; supply and reuse your own to make a retry safe.
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")
            **kwargs: Additional parameters for the charge object

        Returns:
            Async payment result containing request_id, status, and charge_id.

        Raises:
            TypeError: If ``idempotency_key`` is supplied as a non-string value.
            ValueError: If `merchant` is given outside platform mode or is malformed.
            ApiError: If payment processing fails.
        """
        if idempotency_key is not None and not isinstance(idempotency_key, str):
            raise TypeError(
                f"idempotency_key must be a string or None, got {type(idempotency_key).__name__}"
            )

        headers = self._merchant_headers(merchant)

        try:
            charge = {"price": price}

            if description:
                charge["description"] = description

            if expires_at:
                charge["expires_at"] = expires_at

            for key, value in kwargs.items():
                if key not in ["customer"]:
                    charge[key] = value

            resolved_key = (
                idempotency_key
                if idempotency_key and idempotency_key.strip()
                else str(uuid.uuid4())
            )

            request_body = {
                "customer": customer_id,
                "charge": charge,
                "idempotencyKey": resolved_key,
            }

            return self.api.off_session_payment_async(
                request_body, header_params=headers
            )
        except ClientApiError:
            raise
        except Exception as e:
            raise ApiError.from_error(e)

    def refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        cancel_only: Optional[bool] = None,
        merchant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refund a charge.

        The refund is always processed asynchronously: a successful response means the
        request was accepted, and the outcome arrives by webhook (``refund_succeeded``
        or ``refund_failed``). If the same-day cancellation window has not passed the
        charge is cancelled directly; otherwise a bank transfer refund is created.

        Args:
            charge_id: Charge to refund ("trx-*")
            amount: Partial refund amount in JPY. Omit to refund the full amount.
            cancel_only: When True, only attempt cancellation and do not fall back to
                a bank transfer refund. Defaults to the server's behaviour (fallback on).
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            Dict containing ``chargeId`` and ``refundId``.

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If the refund request is rejected
        """
        headers = self._merchant_headers(merchant)

        try:
            request_body: Dict[str, Any] = {"chargeId": charge_id}

            # Both fields are `optional` in the proto: send them only when the caller
            # set them, so the server keeps its own defaults otherwise.
            if amount is not None:
                request_body["amount"] = amount

            if cancel_only is not None:
                request_body["cancelOnly"] = cancel_only

            return self.api.refund(request_body, header_params=headers)
        except ClientApiError:
            raise
        except Exception as e:
            raise ApiError.from_error(e)

    def get(
        self, charge_id: str, merchant: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a charge by ID, or None when it does not exist.

        Args:
            charge_id: Charge ID ("trx-*")
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            Charge data, or None when the charge does not exist. A rejected request
            (400) or an authorization failure (403) raises -- see NOT_FOUND_CODES.

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If the lookup fails for any reason other than not-found
        """
        headers = self._merchant_headers(merchant)

        try:
            return self.api.get_charge(charge_id, header_params=headers)
        except Exception as e:
            if getattr(e, "code", None) in NOT_FOUND_CODES:
                return None
            raise ApiError.from_error(e)

    def list(
        self,
        customer_id: str,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        merchant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List charges for a customer. The response is paginated.

        Args:
            customer_id: Customer ID
            page_size: Number of charges per page
            page_token: Pagination token
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            Charges with pagination info

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If the listing fails
        """
        headers = self._merchant_headers(merchant)

        try:
            return self.api.get_charges(
                customer_id, page_size, page_token, header_params=headers
            )
        except Exception as e:
            raise ApiError.from_error(e)

    def _get_auth_headers(self):
        """Debug method to check what authorization headers are being used"""
        if (
            hasattr(self.api, "api_client")
            and self.api.api_client
            and hasattr(self.api.api_client, "config")
        ):
            config = self.api.api_client.config
            if hasattr(config, "auth_settings") and "oauth2" in config.auth_settings:
                auth_setting = config.auth_settings["oauth2"]
                if callable(auth_setting.get("value")):
                    header_value = auth_setting["value"]()
                    return {auth_setting["key"]: header_value}
        return None
