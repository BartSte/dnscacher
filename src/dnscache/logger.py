import logging
from logging.handlers import RotatingFileHandler


def init(logfile: str, level: str):
    """Initialize the root logger with a rotating file handler.

    Args:
        logfile (str): Path to the log file.
        level (str): Log level to set.

    """
    logger = logging.getLogger()
    level = getattr(logging, level)
    file = RotatingFileHandler(
        logfile, maxBytes=1 * 1024 * 1024, backupCount=5
    )
    stream = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file.setLevel(level)
    file.setFormatter(formatter)

    stream.setLevel(level)
    stream.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file)
    logger.addHandler(stream)
