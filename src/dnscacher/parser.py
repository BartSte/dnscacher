import sys
from argparse import (
    Action,
    ArgumentError,
    ArgumentParser,
    RawDescriptionHelpFormatter,
)
from os.path import join
from typing import override

from dnscacher import paths
from dnscacher.enums import Command
from dnscacher.settings import Settings

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

_DESCRIPTION_GET = """
Only retrieve the mappings from cache and write them to stdout. The output
format is controlled by the `--output` option. By the default, no output is
written to stdout.
"""


class Parser:
    """Parser that merges the namespaces of the parser and its subparsers into
    one namespace by doing two passes over the arguments.

    Attributes:
        subparsers: the list of subparsers that are added to the parser.
    """

    _subparser_parent: ArgumentParser
    parser: ArgumentParser
    subparsers: dict[Command, ArgumentParser]

    def __init__(self):
        """Initialize the parser with the program arguments and subcommands.

        Note that an additional parser is created to handle the subcommands.
        This is done because when the subcommands are added to the main parser,
        is is not straightforward to parse the options and positional arguments
        intermixed, as is described in the argparse documentation. By creating
        a second (hidden) parser, we can parse the options and positional
        arguments separately (and intermixed) and then merge the namespaces of
        the two parsers into one namespace at the end.
        """
        kwargs = dict(
            prog="dnscacher",
            description=_DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
        )
        self.parser = ArgumentParser(**kwargs)  # pyright: ignore
        self.make_subparsers(self.parser)
        self.add_arguments(self.parser)

        self._subparser_parent = ArgumentParser(**kwargs)  # pyright: ignore
        self.subparsers = self.make_subparsers(self._subparser_parent)
        self.add_arguments(list(self.subparsers.values()))

    def add_arguments(self, parsers: ArgumentParser | list[ArgumentParser]):
        """Add the program arguments to the parser that apply to all
        subcommands.

        Args:
            parser: The parser to add the arguments to.

        Returns:
            The same parser to signal that the object is mutated.
        """
        parsers = [parsers] if isinstance(parsers, ArgumentParser) else parsers
        for parser in parsers:
            self._add_arguments(parser)

    def _add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "-o",
            "--output",
            action=_TupleAction,
            help=(
                "Write the obtained data to stdout. Separate multiple outputs "
                "by a comma. Choices: {', '.join(x.value for x in Output)}"
            ),
        )
        parser.add_argument(
            "-i",
            "--ipset",
            help="Name of the ipset to add the IPs to.",
        )
        parser.add_argument(
            "-m",
            "--mappings",
            help="Path to the file with domain→IP mappings.",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            type=int,
            help="Timeout for resolving a domain.",
        )
        parser.add_argument(
            "-j",
            "--jobs",
            type=int,
            help="Number of jobs to run in concurrently (default: 10000).",
        )
        parser.add_argument(
            "-l",
            "--loglevel",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="Set the log level.",
        )
        parser.add_argument("--log", help="Path to the log file.")
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            help="Enable debug mode.",
        )

    def make_subparsers(
        self, parent: ArgumentParser
    ) -> dict[Command, ArgumentParser]:
        """Add the subcommands to the parser.

        Args:
            parser: the parser to add the subcommands to.

        Returns:
            The same parser to signal that the object is mutated.

        """
        commands = parent.add_subparsers(dest="command", required=True)

        subparser_get = commands.add_parser(
            name=Command.GET.value,
            description=_DESCRIPTION_GET,
            formatter_class=RawDescriptionHelpFormatter,
            help=(
                "Only retrieve the current domain-to-ip mappings stored in "
                "cache."
            ),
        )
        subparser_add = commands.add_parser(
            name=Command.ADD.value,
            description=_DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
            help=(
                "Resolve and add the domains from the --source that are not yet"
                "inthe mappings"
            ),
        )
        subparser_add.add_argument(
            "source",
            nargs="?",  # nargs=1 enforced in the parse_args method
            action=_SourceAction,
            help=(
                "URL or file path that contains the domains. Will be ignored if"
                " the `--debug` option is set."
            ),
        )

        subparser_update = commands.add_parser(
            name=Command.UPDATE.value,
            description=_DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
            help=(
                "Update the mappings by resolving new domains and removing "
                "domains that are not in the --source."
            ),
        )
        subparser_update.add_argument(
            "source",
            nargs="?",  # nargs=1 enforced in the parse_args method
            action=_SourceAction,
            help=(
                "URL or file path that contains the domains. Will be ignored if"
                " the `--debug` option is set."
            ),
        )

        subparser_refresh = commands.add_parser(
            name=Command.REFRESH.value,
            description=_DESCRIPTION,
            formatter_class=RawDescriptionHelpFormatter,
            help=(
                "Refresh the mappings by re-resolving a percentage of the "
                "stored mappings based on the --part value."
            ),
        )
        subparser_refresh.add_argument(
            "-p",
            "--part",
            type=self._check_part,
            help=(
                "Percentage between 0 and 100 of the stored mappings to "
                "re-resolve."
            ),
        )
        return {
            Command.GET: subparser_get,
            Command.ADD: subparser_add,
            Command.UPDATE: subparser_update,
            Command.REFRESH: subparser_refresh,
        }

    @staticmethod
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

    def parse_args(self) -> Settings:
        """Parse the arguments and merge the namespaces of the parser and its
        subparsers into one namespace.

        Returns:
            The namespace object with the merged namespaces.
        """
        parsed, remaining = self.parser.parse_known_args()

        if not parsed.command:  # pyright: ignore
            raise ArgumentError(
                None, "the following arguments are required: command"
            )

        subparser = self.subparsers[Command(parsed.command)]  # pyright: ignore
        parsed, remaining = subparser.parse_known_args(
            remaining, namespace=parsed
        )

        if remaining:
            raise ArgumentError(
                None, f"unrecognized arguments: {' '.join(remaining)}"
            )

        return Settings.from_namespace(parsed)


class _SourceAction(Action):
    """Check the source argument.

    - If `--debug` option is set, set the source to `debug.txt`.
    - If not, and the source is empty, raise an error.

    Raises:
        ArgumentError: If the source is empty and the `--debug` option is not
        set.

    Note that `sys.argv` is used to check if the `--debug` option instead of
    using the `namespace` object. This is because the parser has multiple
    namespaces that are combined into one namespace after using the parser and
    all the subparsers. By using `sys.argv`, we can check if the `--debug`
    option is set in any of the namespaces.

    """

    @override
    def __call__(self, parser, namespace, values, option_string=None):
        """Set the `namespace.source` attribute.

        Raises:
            ArgumentError: if the source is empty and the `--debug` option is
            not set.
        """
        if hasattr(namespace, "source") and namespace.source:
            return

        if "--debug" in sys.argv:
            values = join(paths.root, "debug.txt")
        elif not values:
            raise ArgumentError(None, "source is required")

        setattr(namespace, self.dest, values)  # pyright: ignore


class _TupleAction(Action):
    @override
    def __call__(self, parser, namespace, values, option_string=None):
        """Convert the list of values into a tuple and set it as an
        attribute."""
        values = values.split(",") if isinstance(values, str) else values
        setattr(namespace, self.dest, tuple(values))  # pyright: ignore
