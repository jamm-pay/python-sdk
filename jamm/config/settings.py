import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, SecretStr


class ClientConfig(BaseModel):
    """Configuration for the Jamm API client."""

    model_config = ConfigDict(validate_assignment=True)

    # Authentication settings
    client_id: str = Field(default_factory=lambda: os.environ.get("JAMM_CLIENT_ID", ""))
    # SecretStr, not str: a config object reaches print(), a logger, a pydantic
    # ValidationError and any traceback frame holding it, and each of those renders the
    # model's repr. A plain str puts the live credential in all of them. SecretStr
    # renders as "**********" and yields the value only through get_secret_value(), so
    # leaking it takes a deliberate call rather than an incidental repr.
    client_secret: SecretStr = Field(
        default_factory=lambda: SecretStr(os.environ.get("JAMM_CLIENT_SECRET", ""))
    )

    # Environment settings
    environment: str = Field(
        default_factory=lambda: os.environ.get("JAMM_ENVIRONMENT", "production")
    )

    # Platform mode: authenticate against the platform identity service and allow
    # operations to target a specific merchant. Requires platform credentials.
    platform: bool = Field(
        default_factory=lambda: os.environ.get("JAMM_PLATFORM", "").lower()
        in ("1", "true", "yes")
    )

    # Filled in from the Environment resolved for `environment` above.
    #
    # api_base_url is inert: nothing reads it. The API host comes from
    # Environment.api_host, so setting this changes nothing -- kept only because it is a
    # public field on a released config. `environment` is what selects the hosts.
    api_base_url: Optional[str] = None
    oauth_base_url: Optional[str] = None
    verify_ssl: bool = True

    # HTTP settings
    timeout: int = 30
    read_timeout: int = 90
    max_retries: int = 3
    backoff_factor: float = 0.5
