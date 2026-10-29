"""Helper utilities for Jamm SDK examples."""

import os
import sys
import time
from typing import Dict, Any

# Add SDK path to Python import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jamm
from faker import Faker


class Helper:
    """Helper class for SDK examples and testing."""

    @staticmethod
    def configure():
        """Configure the Jamm client using environment variables."""
        required_vars = ["ENV", "MERCHANT_CLIENT_ID", "MERCHANT_CLIENT_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print()
            print("Please set the following environment variables:")
            print("export ENV=staging")
            print("export MERCHANT_CLIENT_ID=***")
            print("export MERCHANT_CLIENT_SECRET=********")
            print()
            sys.exit(1)

        return jamm.configure(
            env=os.environ["ENV"],
            client_id=os.environ["MERCHANT_CLIENT_ID"],
            client_secret=os.environ["MERCHANT_CLIENT_SECRET"],
        )

    @staticmethod
    def email():
        """Get test email address."""
        return os.environ.get("EMAIL", "python.test@jamm-pay.jp")

    @staticmethod
    def customer_id():
        """Get test customer ID from environment."""
        return os.environ.get("CUSTOMER", "cus-cunap31boodfkalob1kg")

    @staticmethod
    def generate_buyer(base_email: str = None) -> Dict[str, Any]:
        """Generate realistic buyer data for testing."""
        fake_en = Faker("en_US")
        fake_jp = Faker("ja_JP")
        timestamp = int(time.time())

        # Use provided email or generate one
        if base_email:
            email_parts = base_email.split("@")
            email = f"{email_parts[0]}+{timestamp}@{email_parts[1]}"
        else:
            email = f"test+{timestamp}@jamm-pay.jp"

        return {
            "email": email,
            "name": fake_en.name(),
            "katakana_last_name": fake_jp.last_kana_name(),
            "katakana_first_name": fake_jp.first_kana_name(),
            "address": fake_jp.address(),
            "birth_date": fake_en.date_of_birth(
                minimum_age=20, maximum_age=70
            ).strftime("%Y-%m-%d"),
            "gender": fake_en.random_element(["male", "female"]),
            "force_kyc": False,
            "metadata": {"source": "python_example", "timestamp": str(timestamp)},
        }
