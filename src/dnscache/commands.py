import logging
import sys
from argparse import ArgumentError
from types import TracebackType
from typing import Callable

from dnscache import logger
from dnscache.domains import Domains
from dnscache.enums import Command
from dnscache.exceptions import InvalidCacheError, IpSetError, SettingsError
from dnscache.ipset import IpSet
from dnscache.mappings import Mappings
from dnscache.settings import Settings


def main():
    """Entry point for the application."""
    sys.excepthook = excepthook
    logger.init()

    settings: Settings = Settings.from_cli()
    logger.set(settings.log, settings.loglevel)
    settings.makedirs()

    command: Command = Command(settings.command)
    function: Callable[[Settings], str] = _COMMANDS[command]
    print(function(settings))


def excepthook(
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


def resolve(settings: Settings) -> str:
    """Map the domains from `Settings.source` to IP addresses.

    The mappings are stored in cache and may be returned based on the
    `Settings.output` attribute.

    Args:
        settings: The settings object.

    """
    mappings: Mappings = Mappings(path=settings.mappings)
    mappings.load()

    domains: Domains = Domains()
    domains.update_from_source(settings.source)

    diff: Domains = domains - mappings.domains
    retained: Domains = mappings.domains & domains
    resolve: Domains = retained.make_random_subset(settings.part) | diff
    logging.info("%s domains to resolve", len(resolve))

    mappings.update_by_resolving(resolve, settings.jobs, settings.timeout)
    mappings.save()

    return mappings.print(settings.output)


def retrieve(settings: Settings) -> str:
    """Retrieve the mappings from cache.

    Args:
        settings: The settings object.

    Returns:
        the mappings from cache as a string.

    """
    mappings: Mappings = Mappings(path=settings.mappings)
    mappings.load()

    return mappings.print(settings.output)


def ipset(settings: Settings) -> str:
    """Create the ipset and add the IP addresses.

    Args:
        settings: The settings object.

    Returns:
        the IP addresses in a format suitable for the `ipset restore` command.

    """
    mappings: Mappings = Mappings(path=settings.mappings)
    mappings.load()

    if not settings.ipset:
        raise SettingsError("No ipset name provided")

    ipset: IpSet = IpSet(settings.ipset)
    ipset.add(mappings.ips)
    ipset.make()

    return mappings.print(settings.output)


_COMMANDS: dict[Command, Callable[[Settings], str]] = {
    Command.RESOLVE: resolve,
    Command.RETRIEVE: retrieve,
    Command.IPSET: ipset,
}
