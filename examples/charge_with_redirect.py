"""On-session (redirect) charge example for Jamm SDK."""

import json
from datetime import datetime, timedelta, timezone
from helper import Helper


def main():
    """Create charge with redirect."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    # Calculate expiration date (2 days from now)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    try:
        # Returns a payment link to send the customer to.
        result = client.payments.on_session(
            customer_id=customer_id,
            price=100,
            description="Test charge with redirect from Python SDK",
            redirect_urls={
                "success_url": "https://example.com/success",
                "failure_url": "https://example.com/fail",
            },
            expires_at=expires_at,
        )
        # Business failures come back in the response, not as an exception.
        if not result.get("success"):
            error = result.get("error") or {}
            print(f"Payment session failed: {error.get('code')} {error.get('message')}")
            raise SystemExit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating charge with redirect: {e}")


if __name__ == "__main__":
    main()
