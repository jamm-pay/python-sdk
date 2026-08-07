from enum import Enum

# Prefer relative import to avoid issues when package installed ("jamm" is top-level package)
try:
    from ..version import VERSION as __version__
except ImportError:
    # Fallback if relative import context changes (e.g., direct script execution)
    from jamm.version import VERSION as __version__


class EnvironmentType(str, Enum):
    PRODUCTION = "production"
    PROD = "prod"
    PRD = "prd"
    LOCAL = "local"
    # Allow any other environment string

    @classmethod
    def _missing_(cls, value):
        # Allow any environment string
        # This makes the Enum accept any value
        return value


class Environment:
    """Environment settings for Jamm SDK"""

    version = __version__

    def __init__(self, env=None, platform: bool = False):
        """
        Initialize environment

        Args:
            env: String environment name ('production', 'local', or custom env name)
            platform: Authenticate against the platform identity service instead of
                the merchant one. Platform and merchant modes are separate services.
        """
        self.type = env or "production"
        self.platform = bool(platform)

        # Platform and merchant modes authenticate against different identity services.
        identity = "platform-identity" if self.platform else "merchant-identity"

        # Set environment-specific URLs
        if self.type in (
            EnvironmentType.PRODUCTION,
            EnvironmentType.PROD,
            EnvironmentType.PRD,
        ):
            self.oauth_base = f"https://{identity}.jamm-pay.jp"
            self.api_host = "api.jamm-pay.jp"
            self.verify_ssl = True
        elif self.type == EnvironmentType.LOCAL:
            self.oauth_base = f"https://{identity}.develop.jamm-pay.jp"
            self.api_host = "api.jamm.test"
            self.verify_ssl = False
        else:
            # Custom environment (staging, develop, etc.)
            self.oauth_base = f"https://{identity}.{self.type}.jamm-pay.jp"
            self.api_host = f"api.{self.type}.jamm-pay.jp"
            self.verify_ssl = True
