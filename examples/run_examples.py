"""Run all Jamm SDK examples."""

import os
import sys
import subprocess
import argparse


def run_example(script_name):
    """Run a single example script."""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.returncode != 0:
            print(f"Exit code: {result.returncode}")

    except Exception as e:
        print(f"Failed to run {script_name}: {e}")


def main():
    """Run examples based on command line arguments."""
    parser = argparse.ArgumentParser(description="Run Jamm SDK examples")
    parser.add_argument(
        "--example",
        help="Specific example to run (e.g., healthcheck, customer, charge, contract)",
    )
    parser.add_argument("--list", action="store_true", help="List available examples")

    args = parser.parse_args()

    # Available examples
    examples = {
        "healthcheck": ["healthcheck_ping.py"],
        "customer": [
            "customer_get.py",
            "customer_get_contract.py",
            "customer_update.py",
            "customer_delete.py",
        ],
        "charge": [
            "charge_without_redirect.py",
            "charge_with_redirect.py",
            "charge_list.py",
        ],
        "contract": [
            "contract_without_charge.py",
            "contract_with_charge.py",
            "contract_get.py",
        ],
        # Needs CHARGE / MERCHANT + PLATFORM_CLIENT_* respectively; each script says so
        # and exits cleanly when they are unset.
        "refund": ["refund.py"],
        "platform": ["platform_payment.py"],
    }

    if args.list:
        print("Available examples:")
        for category, scripts in examples.items():
            print(f"\n{category}:")
            for script in scripts:
                print(f"  - {script}")
        return

    # Check environment variables. The platform category authenticates with platform
    # credentials against a different identity service, so demanding MERCHANT_CLIENT_*
    # there would block the very example the documented variables are meant to run.
    if args.example == "platform":
        required_env_vars = [
            "ENV",
            "PLATFORM_CLIENT_ID",
            "PLATFORM_CLIENT_SECRET",
            "MERCHANT",
        ]
        hints = [
            "export ENV=staging",
            "export PLATFORM_CLIENT_ID=your_platform_client_id",
            "export PLATFORM_CLIENT_SECRET=your_platform_client_secret",
            "export MERCHANT=mer-the_merchant_to_act_for",
        ]
    else:
        required_env_vars = ["ENV", "MERCHANT_CLIENT_ID", "MERCHANT_CLIENT_SECRET"]
        hints = [
            "export ENV=staging",
            "export MERCHANT_CLIENT_ID=your_client_id",
            "export MERCHANT_CLIENT_SECRET=your_client_secret",
            "export CUSTOMER=cus-your_customer_id  # Required by examples that act on an existing customer",
            "export CHARGE=trx-your_charge_id  # Optional, for the refund example",
        ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set them before running examples:")
        for hint in hints:
            print(hint)
        return

    # Run specific example or all examples
    if args.example:
        if args.example in examples:
            for script in examples[args.example]:
                run_example(script)
        else:
            print(f"Unknown example: {args.example}")
            print("Use --list to see available examples")
    else:
        # Run all examples
        print("Running all Jamm SDK examples...")
        # MERCHANT belongs in this check alongside the credentials: platform_payment.py
        # reads it unconditionally, so a sweep without it fails on KeyError rather than
        # skipping the category.
        missing_platform_vars = [
            var
            for var in ("PLATFORM_CLIENT_ID", "PLATFORM_CLIENT_SECRET", "MERCHANT")
            if not os.getenv(var)
        ]
        for category, scripts in examples.items():
            # The platform example needs its own credentials; skip rather than run it
            # into a guaranteed failure during a merchant-credentialed sweep.
            if category == "platform" and missing_platform_vars:
                print(
                    f"\n# Skipping {category.upper()}: "
                    f"{', '.join(missing_platform_vars)} not set"
                )
                continue
            print(f"\n{'#'*60}")
            print(f"# {category.upper()} EXAMPLES")
            print(f"{'#'*60}")
            for script in scripts:
                run_example(script)


if __name__ == "__main__":
    main()
