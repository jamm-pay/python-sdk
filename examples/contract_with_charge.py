"""Create contract with charge example for Jamm SDK."""

import json
from datetime import datetime, timedelta, timezone
from helper import Helper


def main():
    """Create contract with initial charge."""
    # Configure client
    client = Helper.configure()

    # Generate buyer data
    buyer_data = Helper.generate_buyer(Helper.email())

    # Calculate expiration date (2 days from now)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    try:
        # A new customer signs up and pays the first charge through the returned link.
        result = client.payments.on_session(
            buyer=buyer_data,
            price=100,
            description="Initial charge from Python SDK",
            redirect_urls={
                "success_url": "https://example.com/success",
                "failure_url": "https://example.com/fail",
            },
            expires_at=expires_at,
        )
        # Business failures come back in the response, not as an exception.
        if not result.get("success"):
            error = result.get("error") or {}
            print(f"Contract session failed: {error.get('code')} {error.get('message')}")
            raise SystemExit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating contract with charge: {e}")


if __name__ == "__main__":
    main()
