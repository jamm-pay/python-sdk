"""Platform mode example for Jamm SDK.

Platform credentials can call the API on behalf of a merchant. Merchant-scoped
operations accept a `merchant` argument; it is rejected locally unless the client was
configured with `platform=True`. The bank and branch lookups are merchant-agnostic
reference data and take no `merchant`.

Usage:
    export ENV=staging
    export PLATFORM_CLIENT_ID=***
    export PLATFORM_CLIENT_SECRET=********
    export MERCHANT=mer-...
    python examples/platform_payment.py
"""

import json
import os
import sys

# Add SDK path to Python import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jamm
from helper import Helper


def configure():
    """Configure a platform-mode client from environment variables."""
    required = ["ENV", "PLATFORM_CLIENT_ID", "PLATFORM_CLIENT_SECRET", "MERCHANT"]
    missing = [name for name in required if not os.getenv(name)]

    if missing:
        print()
        print("Please set the following environment variables:")
        print("export ENV=staging")
        print("export PLATFORM_CLIENT_ID=***")
        print("export PLATFORM_CLIENT_SECRET=********")
        print("export MERCHANT=mer-...")
        print()
        sys.exit(1)

    return jamm.configure(
        env=os.environ["ENV"],
        client_id=os.environ["PLATFORM_CLIENT_ID"],
        client_secret=os.environ["PLATFORM_CLIENT_SECRET"],
        platform=True,
    )


def main():
    """Act on behalf of a merchant."""
    client = configure()
    merchant = os.environ["MERCHANT"]

    # Only the mode is printed. Nothing reachable from the client's config is echoed,
    # since that object also holds the client secret. Platform mode authenticates
    # against a separate `platform-identity.*` service -- see the SDK README.
    print(f"Mode: {client.mode.value}")
    print()

    try:
        # Verify connectivity for this merchant's scope.
        client.healthcheck(merchant=merchant)
        print(f"Healthcheck ok for {merchant}")

        # Create a payment session on the merchant's behalf.
        result = client.payments.on_session(
            buyer=Helper.generate_buyer(),
            price=1000,
            description="Platform payment example",
            redirect_urls={
                "success_url": "https://example.com/success",
                "failure_url": "https://example.com/failure",
            },
            merchant=merchant,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except ValueError as e:
        # Raised locally when merchant is malformed, or used outside platform mode.
        print(f"Invalid merchant: {e}")
        return 1
    except Exception as e:
        print(f"Error calling on behalf of {merchant}: {e}")
        return 1


if __name__ == "__main__":
    # Exit non-zero on failure: returning normally would let a shell wrapper read a
    # failed healthcheck or payment as success.
    raise SystemExit(main())
