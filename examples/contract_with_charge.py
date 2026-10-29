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
        # Create contract with charge
        result = client.contracts.create_with_charge(
            buyer=buyer_data,
            charge={
                "price": 100,
                "description": "Initial charge from Python SDK",
                "expires_at": expires_at,
            },
            redirect={
                "success_url": "https://jamm-pay.jp/success",
                "failure_url": "https://jamm-pay.jp/fail",
            },
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating contract with charge: {e}")


if __name__ == "__main__":
    main()
