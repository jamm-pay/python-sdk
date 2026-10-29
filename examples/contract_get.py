"""Get contract example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Get contract information."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    try:
        # Get contract
        contract = client.contracts.get(customer_id)
        if contract:
            print(json.dumps(contract, indent=2, ensure_ascii=False))
        else:
            print("No contract found")
    except Exception as e:
        print(f"Error getting contract: {e}")


if __name__ == "__main__":
    main()
