from typing import Dict, Any, Optional
from .api.client import ApiClient
from .payment import Payment


class Charge:
    """High-level charge operations.

    A thin view over :class:`~jamm.payment.Payment` so charge lookups behave
    identically however they are reached, plus the lazy ``iter()`` helper.
    """

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.payment = Payment(api_client)
        self.api = self.payment.api

    def get(
        self, charge_id: str, merchant: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific charge

        Args:
            charge_id: Charge ID
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            Charge data, or None when the charge is not found.

        Raises:
            ApiError: If the lookup fails for any reason other than not-found
        """
        return self.payment.get(charge_id, merchant=merchant)

    def list(
        self,
        customer_id: str,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None,
        merchant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List charges for a customer

        Args:
            customer_id: Customer ID
            page_size: Number of charges per page
            page_token: Pagination token
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            List of charges with pagination info

        Raises:
            ApiError: If charge listing fails
        """
        return self.payment.list(
            customer_id,
            page_size=page_size,
            page_token=page_token,
            merchant=merchant,
        )

    def refund(
        self,
        charge_id: str,
        amount: Optional[int] = None,
        cancel_only: Optional[bool] = None,
        merchant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refund a charge. See :meth:`jamm.payment.Payment.refund`.
        """
        return self.payment.refund(
            charge_id,
            amount=amount,
            cancel_only=cancel_only,
            merchant=merchant,
        )

    def iter(
        self,
        customer_id: str,
        page_size: int = 50,
        start_page_token: Optional[str] = None,
        limit: Optional[int] = None,
        merchant: Optional[str] = None,
    ):
        """Iterate through all charges for a customer.

        Args:
            customer_id: Customer ID.
            page_size: Page size per request (default 50).
            start_page_token: Optional starting page token.
            limit: Optional max number of charges to yield.
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*").

        Yields:
            Individual charge dicts.
        """
        yielded = 0
        token = start_page_token
        seen_tokens = set()

        while True:
            if token in seen_tokens:
                # Protect against accidental server token loops
                break
            if token:
                response = self.list(
                    customer_id,
                    page_size=page_size,
                    page_token=token,
                    merchant=merchant,
                )
            else:
                response = self.list(
                    customer_id, page_size=page_size, merchant=merchant
                )

            charges = []
            next_token = None

            if isinstance(response, dict):
                charges = response.get("charges", []) or []
                # Support pagination shape: response["pagination"]["nextPageToken"] or flat key
                pagination = response.get("pagination")
                if isinstance(pagination, dict):
                    next_token = pagination.get("nextPageToken") or pagination.get(
                        "next_page_token"
                    )
                else:
                    next_token = response.get("nextPageToken") or response.get(
                        "next_page_token"
                    )

            for charge in charges:
                yield charge
                yielded += 1
                if limit is not None and yielded >= limit:
                    return

            if not next_token:
                break
            seen_tokens.add(token)
            token = next_token

    def _get_auth_headers(self):
        """Debug method to check what authorization headers are being used"""
        return self.payment._get_auth_headers()
