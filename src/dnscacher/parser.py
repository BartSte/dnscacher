from argparse import (
    Action,
    ArgumentError,
    ArgumentParser,
    Namespace,
    RawDescriptionHelpFormatter,
)
from os.path import join
from typing import override

from dnscacher import paths
from dnscacher.enums import Command, Output

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


class Parser(ArgumentParser):
    @override
    def parse_args(self, *args, **kwargs) -> Namespace:
        return self._set_source(super().parse_args(*args, **kwargs))

    def _set_source(self, args: Namespace) -> Namespace:
        """Set the source to `debug.txt` if the `--debug` flag is set.

        Args:
            args: The parsed arguments.

        Raises:
            ArgumentError: if the `--debug` flag is not set and no source is
            provided.

        Returns:
            The parsed arguments.

        """
        if not hasattr(args, "source"):
            return args

        if args.debug:
            args.source = join(paths.root, "debug.txt")
        elif not args.source:
            raise ArgumentError(None, "source is required")

        return args


class TupleAction(Action):
    @override
    def __call__(self, parser, namespace, values, option_string=None):
        """Convert the list of values into a tuple and set it as an
        attribute."""
        values = values.split(",") if isinstance(values, str) else values
        setattr(namespace, self.dest, tuple(values))  # pyright: ignore


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


def make_parser() -> Parser:
    """Initialize the parser with program arguments."""
    parser = Parser(
        prog="dnscacher",
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o",
        "--output",
        action=TupleAction,
        help=(
            "Write the obtained data to stdout. Separate multiple outputs by a"
            f"comma. Choices: {', '.join(x.value for x in Output)}"
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
        name=Command.GET.value,
        description=_DESCRIPTION_RETRIEVE,
        formatter_class=RawDescriptionHelpFormatter,
        help="Only retrieve the current domain-to-ip mappings stored in cache.",
    )
    add_command: Parser = commands.add_parser(
        name=Command.ADD.value,
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
        help=(
            "Resolve and add the domains from the --source that are not yet in "
            "the mappings"
        ),
    )
    add_command.add_argument(
        "source",
        nargs="?",  # nargs=1 is enforced in the Parser.parse_args method
        help=(
            "URL or file path that contains the domains. Will be ignored if "
            "the `--debug` option is set."
        ),
    )

    update_command: Parser = commands.add_parser(
        name=Command.UPDATE.value,
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
        help=(
            "Update the mappings by resolving new domains and removing domains "
            "that are not in the --source."
        ),
    )
    update_command.add_argument(
        "source",
        nargs="?",  # nargs=1 is enforced in the Parser.parse_args method
        help=(
            "URL or file path that contains the domains. Will be ignored if "
            "the `--debug` option is set."
        ),
    )

    commands.add_parser(
        name=Command.REFRESH.value,
        description=_DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
        help=(
            "Refresh the mappings by re-resolving a percentage of the stored "
            "mappings based on the --part value."
        ),
    )

    return parser
