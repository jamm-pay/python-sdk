"""List charges example for Jamm SDK."""

import json
from helper import Helper


def main():
    """List charges for a customer."""
    # Configure client
    client = Helper.configure()

    # Get customer ID from environment
    customer_id = Helper.customer_id()

    try:
        # List charges
        result = client.charges.list(customer_id=customer_id, page_size=10)

        if result is None or not result.get("charges"):
            print("No charges found")
            return

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error listing charges: {e}")


if __name__ == "__main__":
    main()
