from typing import Dict, Any, Optional
from .api.client import ApiClient
from .customer import Customer


class Contract:
    """High-level contract operations.

    A thin view over :class:`~jamm.customer.Customer`, which owns the one
    ``GET /v1/customers/{id}/contract`` implementation. Two copies previously had to be
    kept byte-identical, so a fix applied to one silently diverged from the other.
    """

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.customer = Customer(api_client)
        self.customer_api = self.customer.api

    def get(
        self, customer_id: str, merchant: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get contract for a customer

        Args:
            customer_id: Customer ID
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            Contract data, or None when the customer has no contract.

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If the lookup fails for any reason other than not-found
        """
        return self.customer.get_contract(customer_id, merchant=merchant)

    def _get_auth_headers(self):
        """Debug method to check what authorization headers are being used"""
        return self.customer._get_auth_headers()
