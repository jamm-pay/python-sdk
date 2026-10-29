"""Delete customer example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Delete a test customer."""
    # Configure client
    client = Helper.configure()

    # Create a test customer first
    try:
        buyer_data = Helper.generate_buyer()
        customer = client.customers.create(buyer=buyer_data)
        customer_id = customer["customer"]["id"]
        print(f"Created test customer: {customer_id}")

        # Delete the customer
        result = client.customers.delete(customer_id)
        if result:
            print(f"Successfully deleted customer: {customer_id}")
        else:
            print(f"Failed to delete customer: {customer_id}")

    except Exception as e:
        print(f"Error in customer delete example: {e}")


if __name__ == "__main__":
    main()
