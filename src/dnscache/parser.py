import sys
from argparse import ArgumentError, ArgumentParser, RawDescriptionHelpFormatter
from enum import Enum
from os.path import join

from dnscache import paths
from dnscache.settings import Settings

_DESCRIPTION = """
Resolve the IP addresses of the `source` domains and store the domain to IP
mappings in your cache.

When running the program again, only the domains that are in the `source` but
not in the cache are resolved. Also, domains that are no longer in the `source`
are removed from the cache.

You can update the cache (in random parts) by using the `--part` option. By the
default, no output is written to stdout. You can change this by using the
`--output` option.
"""

# https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn-only/hosts


class Output(Enum):
    IPS = "ips"
    DOMAINS = "domains"
    MAPPINGS = "mappings"

    @classmethod
    def multiple(cls, value: str) -> tuple[Enum, ...]:
        """Return a list of Output values from a comma-separated string.

        Args:
            value (str): Comma-separated string of Output values.

        Returns:
            list[Self]: List of Output values.

        """
        values: list[str] = value.replace(",", " ").split()
        return tuple(cls(v) for v in values)


class Parser(ArgumentParser):
    """Custom argument parser for update-blocklist."""

    def __init__(self):
        """Initialize the parser with program arguments."""
        super().__init__(
            prog="dnscache",
            description=_DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
        )
        self.add_argument(
            "source",
            nargs="?",
            default=Settings.source,
            type=self._str_or_debug,
            help="URL or file path that contains the domains.",
        )
        self.add_argument(
            "--output",
            nargs="?",
            type=Output.multiple,
            help=(
                f"Write the obtained data to stdout. Choices: "
                f"{', '.join(x.value for x in Output)} (default: no output)."
            ),
        )
        self.add_argument(
            "-j",
            "--jobs",
            type=int,
            help="Number of jobs to run in parallel.",
            default=Settings.jobs,
        )
        self.add_argument(
            "-l",
            "--loglevel",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set the log level.",
            default=Settings.loglevel,
        )
        self.add_argument(
            "-m",
            "--mappings",
            help="Path to the file with domain→IP mappings.",
            default=Settings.mappings,
        )
        self.add_argument(
            "-i",
            "--ipset",
            help="Name of the ipset to add the IPs to.",
            default=Settings.ipset,
        )
        self.add_argument(
            "-p",
            "--part",
            type=self.check_part,
            default=Settings.part,
            help=(
                "Percentage between 0 and 100 of the stored mappings to "
                "re-resolve."
            ),
        )
        self.add_argument(
            "--log", help="Path to the log file.", default=Settings.log
        )
        self.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode.",
            default=Settings.debug,
        )
        self.add_argument(
            "--timeout",
            type=int,
            help="Timeout for resolving a domain.",
            default=Settings.timeout,
        )

    def check_part(self, value: int | str) -> int:
        """Validate the part argument is between 0 and 100.

        Args:
            value (int | str): The input value for part.

        Returns:
            int: The validated integer value.

        Raises:
            ArgumentError: If the value is not between 0 and 100.

        """
        value = int(value)
        if not 0 <= value <= 100:
            raise ArgumentError(None, "part must be between 0 and 100")
        return value

    def _str_or_debug(self, value: str) -> str:
        """Return the `debug.txt` path if the `--debug` option is set on the
        command line.

        Args:
            value: The input value.

        Returns:
            str: The input value or the `debug.txt` path.

        """
        value = join(paths.root, value) if "--debug" in sys.argv else value
        if not value:
            raise ArgumentError(None, "source must be specified")
        return value
