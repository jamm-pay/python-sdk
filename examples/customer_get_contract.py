"""Get customer contract example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Get customer contract information."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    try:
        # Get customer contract
        contract = client.customers.get_contract(customer_id)
        if contract:
            print(json.dumps(contract, indent=2, ensure_ascii=False))
        else:
            print("No contract found for customer")
    except Exception as e:
        print(f"Error getting customer contract: {e}")


if __name__ == "__main__":
    main()
