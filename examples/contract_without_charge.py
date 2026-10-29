"""Create contract without charge example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Create contract without initial charge."""
    # Configure client
    client = Helper.configure()

    # Generate buyer data
    buyer_data = Helper.generate_buyer(Helper.email())

    try:
        # Create contract without charge
        result = client.contracts.create_without_charge(
            buyer=buyer_data,
            redirect={
                "success_url": "https://jamm-pay.jp/success",
                "failure_url": "https://jamm-pay.jp/fail",
            },
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating contract without charge: {e}")


if __name__ == "__main__":
    main()
