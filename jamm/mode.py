"""SDK operation modes."""

from enum import Enum


class Mode(str, Enum):
    """How the SDK authenticates and whom it acts for.

    - ``MERCHANT``: standard direct API access with merchant credentials.
    - ``PLATFORM``: platform credentials that may call the API on behalf of a
      merchant. Only in this mode may an operation take a ``merchant`` argument.
    """

    MERCHANT = "merchant"
    PLATFORM = "platform"


__all__ = ["Mode"]
