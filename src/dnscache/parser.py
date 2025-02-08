import sys
from argparse import (
    ArgumentError,
    ArgumentParser,
    RawDescriptionHelpFormatter,
)
from os.path import join

from dnscache import paths
from dnscache.enums import Command, Output

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

_DESCRIPTION_RETRIEVE = """
Only retrieve the mappings from cache and write them to stdout. The output
format is controlled by the `--output` option. By the default, no output is
written to stdout.
"""

# https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn-only/hosts


def _check_part(value: int | str) -> int:
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


def _str_or_debug(value: str) -> str:
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


def make_parser() -> ArgumentParser:
    """Initialize the parser with program arguments."""
    parser = ArgumentParser(
        prog="dnscache",
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        type=Output.multiple,
        help=(
            f"Write the obtained data to stdout. Choices: "
            f"{', '.join(x.value for x in Output)} (default: no output)."
        ),
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Number of jobs to run in parallel.",
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the log level.",
    )
    parser.add_argument(
        "-m",
        "--mappings",
        help="Path to the file with domain→IP mappings.",
    )
    parser.add_argument(
        "-i",
        "--ipset",
        help="Name of the ipset to add the IPs to.",
    )
    parser.add_argument(
        "-p",
        "--part",
        type=_check_part,
        help=(
            "Percentage between 0 and 100 of the stored mappings to "
            "re-resolve."
        ),
    )
    parser.add_argument("--log", help="Path to the log file.")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        help="Timeout for resolving a domain.",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser(
        name=Command.RETRIEVE.value,
        description=_DESCRIPTION_RETRIEVE,
        formatter_class=RawDescriptionHelpFormatter,
        help="Only retrieve the current domain-to-ip mappings stored in cache.",
    )
    resolve_parser: ArgumentParser = commands.add_parser(
        name=Command.RESOLVE.value,
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
        help=(
            "Resolve the IP addresses of the domains and store the resulting "
            "domain-to-ip mappings in cache."
        ),
    )
    resolve_parser.add_argument(
        "source",
        nargs="?",
        type=_str_or_debug,
        help="URL or file path that contains the domains.",
    )

    commands.add_parser(
        name=Command.IPSET.value,
        description=(
            "Create an ipset of the IP addresses in the cache. The ipset is "
            "created with the name provided by the `--ipset` option."
        ),
    )

    return parser
