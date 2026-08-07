from typing import Dict, Any, Optional, Tuple
from .client import ApiClient


class HealthcheckApi:
    """Healthcheck API operations"""

    def __init__(self, api_client: Optional[ApiClient] = None):
        self.api_client = api_client or ApiClient()

    def ping(self, **kwargs) -> Dict[str, Any]:
        """Ping Jamm server to check connection"""
        data, status_code, headers = self.ping_with_http_info(**kwargs)
        return data

    def ping_with_http_info(self, **kwargs) -> Tuple[Any, int, Dict]:
        """Ping with full HTTP info"""
        opts = {
            "return_type": "object",
            # /v1/healthcheck is authenticated: without this the gateway answers
            # "please use either user cookie or authorization header". The legacy
            # HTTPClient that client.healthcheck() ran on merged the auth header into
            # every request, so leaving auth_names off here silently dropped auth the
            # shortcut already had when it moved onto this transport.
            "auth_names": ["oauth2"],
            "accepts": ["application/json"],
            **kwargs,
        }
        return self.api_client.call_api("GET", "/v1/healthcheck", opts)
