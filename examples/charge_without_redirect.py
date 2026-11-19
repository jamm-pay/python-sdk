"""Off-session (no redirect) charge example for Jamm SDK."""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from helper import Helper


def main():
    """Charge an existing customer with an active contract, without redirecting them."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    # Calculate expiration date (2 days from now)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # To retry after a lost response, rerun with IDEMPOTENCY_KEY set to the key printed
    # below; a new key charges again.
    idempotency_key = os.environ.get("IDEMPOTENCY_KEY") or str(uuid.uuid4())
    print(f"idempotency_key: {idempotency_key}")

    try:
        # Asynchronous: returns a charge ID at once; the outcome arrives by webhook.
        result = client.payments.off_session_async(
            customer_id=customer_id,
            price=100,
            description="Test charge from Python SDK",
            expires_at=expires_at,
            idempotency_key=idempotency_key,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating charge: {e}")


if __name__ == "__main__":
    main()
