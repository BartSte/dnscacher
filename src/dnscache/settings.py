import logging
import os
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from ntpath import expandvars
from os import makedirs
from os.path import dirname
from typing import Any, Self

from dnscache.exceptions import SettingsError
from dnscache.helpers import is_root
from dnscache.parser import make_parser


@dataclass
class Settings:
    """Holds settings for the update-blocklist script.

    Attributes:
        source (str): URL or file path for the domains.

        debug (bool): Enable debug mode.
        ipset (str): Name of the ipset.
        jobs (int): Number of parallel jobs.
        log (str): Path to the log file.
        loglevel (str): Logging level.
        mappings (str): File path for domain→IP mappings.
        part (int): Percentage (0-100) of stored mappings to re-resolve.
        timeout (int): Timeout in seconds for resolving a domain.

    """

    command: str = ""
    debug: bool = False
    ipset: str = ""
    jobs: int = 10000
    log: str = ""
    loglevel: str = "INFO"
    mappings: str = ""
    output: tuple[str, ...] = ()
    part: int = 100
    source: str = ""
    timeout: int = 10

    _log_root_unix: str = "/var/log/dnscache.log"
    _log_unix: str = "$HOME/.local/state/dnscache.log"
    _log_win: str = "$TEMP\\dnscache\\dnscache.log"

    _mappings_root_unix: str = "/var/cache/dnscache/mappings.pickle"
    _mappings_unix: str = "$HOME/.cache/dnscache/mappings.pickle"
    _mappings_win: str = "$TEMP\\dnscache\\mappings.pickle"

    def __post_init__(self):
        """Set the default values for the settings."""
        if is_root():
            self._set_root_defaults()
        else:
            self._set_user_defaults()

        self.mappings = expandvars(self.mappings)
        self.log = expandvars(self.log)
        logging.info("Settings: %s", self)

    def _set_root_defaults(self):
        """Set the default values for root."""
        if self.mappings:
            return

        if os.name == "nt":
            self.mappings = self._mappings_win
            self.log = self._log_win
        else:
            self.mappings = self._mappings_root_unix
            self.log = self._log_root_unix

    def _set_user_defaults(self):
        """Set the default values for non-root users."""
        if self.mappings:
            return

        if os.name == "nt":
            self.mappings = self._mappings_win
            self.log = self._log_win
        else:
            self.mappings = self._mappings_unix
            self.log = self._log_unix

    def makedirs(self):
        """Create the directories needed for the settings.

        Creates the parent directory for the mappings file.
        """
        dirs: list[str] = [dirname(self.mappings)]
        for d in dirs:
            logging.info("Trying to create directory %s", d)
            makedirs(d, exist_ok=True)

    @classmethod
    def from_cli(cls) -> Self:
        """Create a new Settings object from the command line arguments.

        Returns:
            The Settings object.

        """
        parser: ArgumentParser = make_parser()
        args: Namespace = parser.parse_args()
        kwargs: dict[str, Any] = {
            key: value for key, value in vars(args).items() if value
        }
        try:
            return cls(**kwargs)
        except TypeError as e:
            raise SettingsError(f"Invalid settings: {e}") from e

    def as_dict(self) -> dict[str, int | str | bool | tuple[str, ...]]:
        """Return the public attributes of the Settings object that are not
        functions or properties.

        Returns:
            list[str]: The public attributes.

        """
        return {
            key: value
            for key, value in self.__annotations__.items()
            if not key.startswith("_")
        }
