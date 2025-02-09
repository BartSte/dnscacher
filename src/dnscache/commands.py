import logging
import sys
from typing import Callable

from dnscache import exceptions, formatter, logger
from dnscache.domains import Domains
from dnscache.ipset import IpSet
from dnscache.mappings import Mappings
from dnscache.settings import Settings


def main():
    """Entry point for the application."""
    sys.excepthook = exceptions.hook
    logger.init()

    settings: Settings = Settings.from_cli()
    logger.set(settings.log, settings.loglevel)
    settings.makedirs()

    print(Commands.run(settings))


class Commands:
    _domains: Domains
    _mappings: Mappings
    _settings: Settings

    def __init__(self, settings: Settings):
        self._domains = Domains()
        self._mappings = Mappings(path=settings.mappings)
        self._settings = settings

    @classmethod
    def run(cls, settings: Settings) -> str:
        """Run the command specified in the settings.

        Args:
            settings: The settings object.

        Returns:
            The output of the command.
        """
        return cls(settings)()

    def __call__(self) -> str:
        """Run the command specified in the settings.

        Returns:
            The output of the command.
        """
        callback: Callable[[], None] = getattr(self, self._settings.command)
        callback()

        ipset: IpSet = IpSet(self._settings.ipset)
        ipset.update(self._mappings.ips)
        return formatter.product(
            [
                self._mappings,
                self._mappings.ips,
                self._mappings.domains,
                ipset,
            ],
            self._settings.output,
        )

    def get(self):
        """Retrieve the mappings from cache.

        Args:
            self.settings: The settings object.

        Returns:
            the mappings from cache as a string.

        """
        self._mappings.load()

    def update(self):
        """Update the mappings by resolving new domains and removing domains
        that are not in the Settings.source."""
        self._add()
        self._remove()

    def _add(self):
        """Same as add, but does not save the mappings"""
        self._mappings.load()

        self._domains.update_from_source(self._settings.source)
        new: Domains = self._domains - self._mappings.domains
        logging.info("Number of new domains: %d", len(new))

        self._mappings.update_by_resolving(
            new, self._settings.jobs, self._settings.timeout
        )

    def _remove(self):
        """Remove domains that are not in the source."""
        remove: Domains = self._mappings.domains - self._domains
        logging.info("Number of removed domains: %d", len(remove))
        for domain in remove:
            self._mappings.pop(domain)

    def add(self):
        """Resolve and add the domains from the Settings.source that are not yet
        in the mappings.

        Args:
            settings: The settings object.


        Returns:
            The output of the command.
        """
        self._add()
        self._mappings.save()

    def refresh(self):
        """Refresh the mappings by re-resolving a percentage of the stored
        mappings based on the Settings.part value."""
        self._mappings.load()
        subset: Domains = self._mappings.domains.make_random_subset(
            self._settings.part
        )
        self._mappings.update_by_resolving(
            subset,
            self._settings.jobs,
            self._settings.timeout,
        )
        self._mappings.save()
