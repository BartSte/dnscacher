import logging
import os
from dataclasses import dataclass
from enum import Enum
from ntpath import expandvars
from os import makedirs
from os.path import dirname, join

from dnscache import paths
from dnscache.helpers import is_root


class SettingsError(Exception):
    """Raised when a setting is missing or invalid."""


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

    source: str = ""
    debug: bool = False
    ipset: str = ""
    jobs: int = 10000
    log: str = ""
    loglevel: str = "INFO"
    mappings: str = ""
    part: int = 100
    timeout: int = 5
    output: tuple[Enum, ...] = ()

    def __post_init__(self):
        """Set the default values for the settings."""
        if is_root():
            self._set_root_defaults()
        else:
            self._set_user_defaults()

        self.mappings = expandvars(self.mappings)
        self.log = expandvars(self.log)

        if self.debug:
            self.source = join(paths.root, "debug.txt")

        if not self.source:
            raise SettingsError("No source specified")

    def _set_root_defaults(self):
        """Set the default values for root."""
        if self.mappings:
            return

        if os.name == "nt":
            self.mappings = "$TEMP\\dnscache\\mappings.pickle"
            self.log = "$TEMP\\dnscache\\dnscache.log"
        else:
            self.mappings = "/var/cache/dnscache/mappings.pickle"
            self.log = "/var/log/dnscache.log"

    def _set_user_defaults(self):
        """Set the default values for non-root users."""
        if self.mappings:
            return

        if os.name == "nt":
            self.mappings = "$TEMP\\dnscache\\mappings.pickle"
            self.log = "$TEMP\\dnscache\\dnscache.log"
        else:
            self.mappings = "$HOME/.cache/dnscache/mappings.pickle"
            self.log = "$HOME/.local/state/dnscache.log"

    def makedirs(self):
        """Create the directories needed for the settings.

        Creates the parent directory for the mappings file.
        """
        dirs: list[str] = [dirname(self.mappings)]
        for d in dirs:
            logging.info("Trying to create directory %s", d)
            makedirs(d, exist_ok=True)
