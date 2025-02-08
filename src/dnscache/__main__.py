import logging
import sys
from argparse import ArgumentError, Namespace

from dnscache import logger
from dnscache.domains import Domains
from dnscache.ipset import IpSetError
from dnscache.mappings import InvalidCacheError, Mappings
from dnscache.parser import Parser
from dnscache.settings import Settings


def main():
    """Main entry point for updating the blocklist.

    Downloads a blocklist from the specified URL, resolves the domains (or a
    subset of them), updates the stored domain→IP mappings, updates the ipset,
    and ensures the iptables rule is in place.
    """
    sys.excepthook = excepthook
    args: Namespace = Parser().parse_args()
    settings: Settings = Settings(**vars(args))

    logger.init(settings.log, settings.loglevel)
    logging.info("Initializing logger")

    settings.makedirs()
    logging.info("Settings: %s", settings)

    mappings: Mappings = Mappings(path=settings.mappings)
    mappings.load()

    domains: Domains = Domains()
    if settings.debug:
        domains.update({"example.com", "example.org"})
    else:
        domains.update_from_url(settings.url)

    diff: Domains = domains - mappings.domains
    retained: Domains = mappings.domains & domains
    resolve: Domains = retained.make_random_subset(settings.part) | diff
    logging.info("%s domains to resolve", len(resolve))

    mappings.update_by_resolving(resolve, settings.jobs, settings.timeout)
    mappings.save()

    print(mappings.print(settings.output))

    # The whole ipset and iptables part does not really belong in this module,
    # right?
    # ipset: IpSet = IpSet(settings.ipset)
    # ipset.make()
    # ipset.add(mappings.ips)
    # ipset.block_persistent()


def excepthook(type_: type[BaseException], value: BaseException, traceback):
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
    )
    if isinstance(value, expected):
        logging.error(value)
    else:
        logging.critical(
            "Unexpected error: ", exc_info=(type_, value, traceback)
        )
    sys.exit(1)


if __name__ == "__main__":
    main()
