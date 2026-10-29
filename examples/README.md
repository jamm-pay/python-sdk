# Jamm Python SDK Examples

This directory contains practical examples demonstrating how to use the Jamm Python SDK.

## Setup

### 1. Install Dependencies

```bash
pip install -e ..
pip install faker  # For generating test data
```

### 2. Set Environment Variables

```bash
export ENV=staging
export MERCHANT_CLIENT_ID=your_client_id
export MERCHANT_CLIENT_SECRET=your_client_secret
export CUSTOMER=cus-your_customer_id  # Optional, for customer-specific examples
export EMAIL=your_test_email@example.com  # Optional
export CHARGE=trx-your_charge_id  # Optional, for refund.py
```

`ENV` selects which Jamm environment the examples run against:

| `ENV` | Host | Who it is for |
| --- | --- | --- |
| `staging` | `api.staging.jamm-pay.jp` | The sandbox. Use this one — staging credentials are what an integration is issued alongside production. |
| `production` | `api.jamm-pay.jp` | Live money. The examples create customers and charges, so point them here only deliberately. |
| `develop` | `api.develop.jamm-pay.jp` | Jamm's internal environment. No credentials are issued for it outside Jamm. |

For the platform mode example, use platform credentials instead:

```bash
export PLATFORM_CLIENT_ID=your_platform_client_id
export PLATFORM_CLIENT_SECRET=your_platform_client_secret
export MERCHANT=mer-the_merchant_to_act_for
```

## Running Examples

### Run All Examples

```bash
python run_examples.py
```

### Run Specific Categories

```bash
python run_examples.py --example healthcheck
python run_examples.py --example customer
python run_examples.py --example charge
python run_examples.py --example contract
python run_examples.py --example refund
python run_examples.py --example platform
```

### Run Individual Examples

```bash
python healthcheck_ping.py
python customer_get.py
python charge_without_redirect.py
```

### List Available Examples

```bash
python run_examples.py --list
```

### Using Make

```bash
make install    # Install dependencies
make run        # Run all examples
make health     # Run health check
make customer   # Run customer examples
make charge     # Run charge examples
make contract   # Run contract examples
```

## Examples Overview

### Health Check

- `healthcheck_ping.py` - Test API connectivity

### Customer Management

- `customer_get.py` - Retrieve customer information
- `customer_get_contract.py` - Get customer's contract
- `customer_update.py` - Update customer data
- `customer_delete.py` - Delete a customer

### Charge Operations

- `charge_without_redirect.py` - Create direct charge
- `charge_with_redirect.py` - Create charge with payment page redirect
- `charge_list.py` - List charges for a customer

### Contract Management

- `contract_without_charge.py` - Create contract without initial payment
- `contract_with_charge.py` - Create contract with initial payment
- `contract_get.py` - Retrieve contract information

## Helper Utilities

The `helper.py` module provides:

- Client configuration from environment variables
- Realistic test data generation using Faker
- Common utility functions for examples

## Notes

- All examples include proper error handling
- Test data is generated with realistic Japanese names and addresses
- Examples follow the same patterns as the Ruby SDK examples
- Set `CUSTOMER` environment variable to use existing customer for testing
- Examples clean up after themselves when appropriate
