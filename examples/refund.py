"""Refund example for Jamm SDK.

The refund is always processed asynchronously: a successful response means the request
was accepted, and the outcome arrives by webhook (`refund_succeeded` / `refund_failed`).

Usage:
    export CHARGE=trx-...
    python examples/refund.py
"""

import json
import os

from helper import Helper


def main():
    """Refund a charge."""
    client = Helper.configure()

    charge_id = os.environ.get("CHARGE")
    if not charge_id:
        print("Please set the charge to refund: export CHARGE=trx-...")
        return

    try:
        # Full refund. If the same-day cancellation window has not passed the charge is
        # cancelled directly; otherwise a bank transfer refund is created.
        result = client.payments.refund(charge_id)
        print("Full refund accepted:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Partial refund of a fixed amount in JPY:
        #   client.payments.refund(charge_id, amount=500)
        #
        # Cancel only, without falling back to a bank transfer refund:
        #   client.payments.refund(charge_id, cancel_only=True)
    except Exception as e:
        print(f"Error refunding charge: {e}")


if __name__ == "__main__":
    main()
