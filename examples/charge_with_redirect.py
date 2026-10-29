"""Create charge with redirect example for Jamm SDK."""

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
        # Create charge with redirect
        result = client.charges.create_with_redirect(
            customer_id=customer_id,
            price=100,
            description="Test charge with redirect from Python SDK",
            success_url="https://jamm-pay.jp/success",
            failure_url="https://jamm-pay.jp/fail",
            expires_at=expires_at,
            metadata={"source": "python_example"},
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating charge with redirect: {e}")


if __name__ == "__main__":
    main()
