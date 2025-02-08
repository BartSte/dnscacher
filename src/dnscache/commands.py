import logging
import sys
from typing import Callable

from dnscache import exceptions, logger, printer
from dnscache.domains import Domains
from dnscache.enums import Command
from dnscache.mappings import Mappings
from dnscache.settings import Settings


def main():
    """Entry point for the application."""
    sys.excepthook = exceptions.hook
    logger.init()

    settings: Settings = Settings.from_cli()
    logger.set(settings.log, settings.loglevel)
    settings.makedirs()

    command: Command = Command(settings.command)
    function: Callable[[Settings], str] = _COMMANDS[command]
    print(function(settings))


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

    return printer.print(mappings, settings.output)


def retrieve(settings: Settings) -> str:
    """Retrieve the mappings from cache.

    Args:
        settings: The settings object.

    Returns:
        the mappings from cache as a string.

    """
    mappings: Mappings = Mappings(path=settings.mappings)
    mappings.load()

    return printer.print(mappings, settings.output)


_COMMANDS: dict[Command, Callable[[Settings], str]] = {
    Command.RESOLVE: resolve,
    Command.RETRIEVE: retrieve,
}
