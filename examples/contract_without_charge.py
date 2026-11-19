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
        # A new customer signs up through the returned link; no charge is made.
        result = client.payments.on_session(
            buyer=buyer_data,
            redirect_urls={
                "success_url": "https://example.com/success",
                "failure_url": "https://example.com/fail",
            },
        )
        # Business failures come back in the response, not as an exception.
        if not result.get("success"):
            error = result.get("error") or {}
            print(f"Contract session failed: {error.get('code')} {error.get('message')}")
            raise SystemExit(1)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating contract without charge: {e}")


if __name__ == "__main__":
    main()
