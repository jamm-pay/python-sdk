"""Create charge without redirect example for Jamm SDK."""

import json
from datetime import datetime, timedelta, timezone
from helper import Helper


def main():
    """Create charge without redirect."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    # Calculate expiration date (2 days from now)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    try:
        # Create charge without redirect
        result = client.charges.create_without_redirect(
            customer_id=customer_id,
            price=100,
            description="Test charge from Python SDK",
            expires_at=expires_at,
            metadata={"source": "python_example"},
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating charge: {e}")


if __name__ == "__main__":
    main()
