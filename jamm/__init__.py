"""Jamm SDK for Python"""

from .import_hook import install

install()

from typing import Any, Dict, Optional
from .client import JammClient
from .customer import Customer
from .contract import Contract
from .charge import Charge
from .payment import Payment
from .healthcheck import Healthcheck
from .bank import Bank, BankBranch
from .webhook import (
    Webhook,
    InvalidSignatureError,
    WebhookMessage,
    ChargeMessage,
    ChargeError,
    ContractMessage,
    RefundInfo,
    UserAccountMessage,
)
from .errors import ApiError  # ← Add this import

# API clients for advanced usage
from .api import (
    ApiClient,
    CustomerApi,
    PaymentApi,
    HealthcheckApi,
    BankApi,
)

# Configuration and environment
from .config.settings import ClientConfig
from .environment.env import Environment
from .mode import Mode

# Enum constants and comparison helpers
from . import types

from .version import VERSION as __version__


def configure(
    env: str,
    client_id: str,
    client_secret: str,
    platform: Optional[bool] = None,
):
    """Configure and return a JammClient instance

    Args:
        env: Environment name ('production', 'local', or custom)
        client_id: API client ID
        client_secret: API client secret
        platform: Enable platform mode -- authenticates against the platform identity
            service and lets each operation take a `merchant` argument. Requires
            platform credentials. Defaults to None, meaning "not specified", so the
            JAMM_PLATFORM environment variable decides; a literal False forces merchant
            mode regardless of the environment.
    """
    return JammClient.configure(client_id, client_secret, env, platform=platform)


# Main public API - high-level classes
__all__ = [
    # Main client and configuration
    "JammClient",
    "configure",
    # High-level operation classes
    "Customer",
    "Contract",
    "Charge",
    "Payment",
    "Healthcheck",
    "Bank",
    "BankBranch",
    "Webhook",
    # Webhook message classes
    "WebhookMessage",
    "ChargeMessage",
    "ChargeError",
    "ContractMessage",
    "RefundInfo",
    "UserAccountMessage",
    # Exceptions
    "InvalidSignatureError",
    "ApiError",
    # Advanced API clients
    "ApiClient",
    "CustomerApi",
    "PaymentApi",
    "HealthcheckApi",
    "BankApi",
    # Configuration
    "ClientConfig",
    "Environment",
    "Mode",
    # Enum constants and comparison helpers
    "types",
    # Version
    "__version__",
]


# Convenience methods for quick setup
def ping(merchant: Optional[str] = None) -> Dict[str, Any]:
    """Quick healthcheck ping.

    Uses credentials from the environment (JAMM_CLIENT_ID / JAMM_CLIENT_SECRET /
    JAMM_ENVIRONMENT). Call `configure()` instead when passing credentials explicitly.

    Args:
        merchant: Platform mode only -- verify connectivity for this merchant's scope.
    """
    # Instantiate: Healthcheck.ping is an instance method, and calling it on the class
    # raised TypeError, so this entry point never worked.
    return Healthcheck(JammClient().api_client).ping(merchant=merchant)
