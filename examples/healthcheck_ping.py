"""Health check example for Jamm SDK."""

import json
from helper import Helper


def main():
    """Test health check endpoint."""
    # Configure client
    client = Helper.configure()

    # Perform health check
    response = client.healthcheck()

    # Print response
    print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
