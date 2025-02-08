import logging
import sys
from argparse import ArgumentError
from types import TracebackType


class InvalidCacheError(Exception):
    """Raised when the mappings cache file is invalid."""


class IpSetError(Exception):
    """Raised when an error occurs during ipset operations."""


class SettingsError(Exception):
    """Raised when a setting is missing or invalid."""


def hook(
    type_: type[BaseException],
    value: BaseException,
    traceback: TracebackType | None,
):
    """Global exception hook.

    Logs errors based on type and then exits.

    Args:
        type_ (type[BaseException]): The exception class.
        value (BaseException): The exception instance.
        traceback: Traceback object.

    """
    expected: tuple[type[BaseException], ...] = (
        KeyboardInterrupt,
        InvalidCacheError,
        ArgumentError,
        IpSetError,
        SettingsError,
    )
    if isinstance(value, expected):
        logging.error(value)
    else:
        logging.critical(
            "Unexpected error: ", exc_info=(type_, value, traceback)
        )
    sys.exit(1)
