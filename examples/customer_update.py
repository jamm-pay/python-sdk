"""Update customer example for Jamm SDK."""

import json
import time
from helper import Helper


def main():
    """Update customer information."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    try:
        # Update customer
        updated_customer = client.customers.update(
            customer_id=customer_id,
            data={
                "name": "Updated Customer Name",
                "metadata": {
                    "updated_at": str(int(time.time())),
                    "source": "python_example_update",
                },
            },
        )
        print(json.dumps(updated_customer, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error updating customer: {e}")


if __name__ == "__main__":
    main()
