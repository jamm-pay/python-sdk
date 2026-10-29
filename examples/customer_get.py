"""Get customer example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Get customer information."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    try:
        # Get customer
        customer = client.customers.get(customer_id)
        print(json.dumps(customer, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error getting customer: {e}")


if __name__ == "__main__":
    main()
