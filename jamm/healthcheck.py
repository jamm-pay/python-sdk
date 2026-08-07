from typing import Dict, Any, Optional
from .api.healthcheck_api import HealthcheckApi
from .api.client import ApiClient
from .errors import ApiError


class Healthcheck:
    """Health check operations"""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api = HealthcheckApi(api_client)

    def ping(self, merchant: Optional[str] = None) -> Dict[str, Any]:
        """
        Ping the Jamm server to check connectivity

        Args:
            merchant: Platform mode only -- verify connectivity for this merchant's
                scope ("mer-*")

        Returns:
            Healthcheck response

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed
            ApiError: If ping fails
        """
        headers = self.api.api_client.merchant_headers(merchant)

        try:
            return self.api.ping(header_params=headers)
        except Exception as e:
            raise ApiError.from_error(e)

    def check(self, merchant: Optional[str] = None) -> bool:
        """
        Simple boolean health check

        Args:
            merchant: Platform mode only -- act on behalf of this merchant ("mer-*")

        Returns:
            True if service is healthy, False otherwise

        Raises:
            ValueError: If `merchant` is given outside platform mode or is malformed.
                A local argument error is the caller's bug, not an outage, so it is
                raised rather than reported as an unhealthy service.
        """
        # Validate before the try: a bad merchant must not be reportable as downtime.
        self.api.api_client.merchant_headers(merchant)

        try:
            self.ping(merchant=merchant)
            return True
        except Exception:
            return False

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
