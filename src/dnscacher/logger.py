import logging
import sys
from logging.handlers import RotatingFileHandler

_stderr_write = sys.stderr.write


def init():
    """Initialize the root logger with a rotating file handler.

    Args:
        logfile (str): Path to the log file.
        level (str): Log level to set.

    """
    logger = logging.getLogger()
    stream = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream.setFormatter(formatter)
    logger.addHandler(stream)


def set(logfile: str, level: str):
    """Set the log file and level for the root logger.

    Args:
        logfile (str): Path to the log file.
        level (str): Log level to set.

    """
    logger = logging.getLogger()
    level = getattr(logging, level)
    file = RotatingFileHandler(logfile, maxBytes=1 * 1024 * 1024, backupCount=5)

    file.setLevel(level)
    file.setFormatter(logger.handlers[0].formatter)

    logger.setLevel(level)
    logger.addHandler(file)
    logging.info("--- New run ---")


def set_quiet(quiet: bool):
    """Suppress output to stderr.

    Args:
        quiet (bool): Suppress output to stderr.

    """
    if quiet:
        sys.stderr.write = lambda *args, **kwargs: None  # pyright: ignore
    else:
        sys.stderr.write = _stderr_write
