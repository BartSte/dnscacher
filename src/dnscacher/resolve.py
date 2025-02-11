import asyncio
import logging
import socket
from asyncio import Semaphore
from collections.abc import Coroutine

from aiodns import DNSResolver
from aiodns.error import DNSError
from pygeneral.print.bar import ProgressBar

from dnscacher.domains import Domains


class Resolver:
    _excluded: set[str]
    _semaphore: Semaphore
    _timeout: int

    def __init__(
        self,
        jobs: int = 10000,
        timeout: int = 5,
        excluded: set[str] | None = None,
    ):
        """Initialize.

        Args:
            jobs (int, optional): Maximum number of concurrent resolutions.
            timeout (int, optional): Timeout for each resolution.

        """
        self._timeout = timeout
        self._excluded = excluded or set()
        self._semaphore = Semaphore(jobs)

    async def fetch_ips(
        self, domains: Domains, mappings: dict[str, list[str]] | None = None
    ):
        """Resolve multiple domains concurrently.

        Args:
            domains (Domains): Set of domains to resolve.
            mappings (dict[str, list[str]], optional): object to update

        """
        dns = DNSResolver()
        mappings = mappings or {}
        tasks: list[Coroutine[None, None, tuple[str, list[str]]]] = [
            self._fetch_ip(domain, dns) for domain in domains
        ]
        logging.info("Resolving %s domains async", len(tasks))

        progress = ProgressBar(
            max_value=len(tasks),
            prefix="Resolving: ",
            suffix=f" (0/{len(tasks)}) domains",
        )

        for i, future in enumerate(asyncio.as_completed(tasks)):
            domain, ips = await future
            mappings[domain] = self._filter_ips(ips)
            progress.suffix = f" ({i+1}/{len(tasks)}) domains"
            progress.value += 1

        logging.info("Resolved %s domains", len(mappings))
        return mappings

    async def _fetch_ip(
        self, domain: str, dns_resolver: DNSResolver | None = None
    ) -> tuple[str, list[str]]:
        """Asynchronously resolve a single domain to its IPv4 addresses.

        Args:
            domain (str): The domain to resolve.
            dns (DNSResolver, optional): DNSResolver instance. Defaults to None,
            which creates a new instance.

        Returns:
            A tuple containing the domain and a list of resolved IPs.

        """
        dns_resolver = dns_resolver or DNSResolver()
        async with self._semaphore:
            try:
                result = await asyncio.wait_for(
                    dns_resolver.gethostbyname(domain, socket.AF_INET),
                    timeout=self._timeout,
                )
                ips = self._filter_ips(result.addresses)  # pyright: ignore
                return domain, ips
            except asyncio.TimeoutError:
                logging.debug("Timeout resolving %s", domain)
                return domain, []
            except DNSError as e:
                logging.debug("Error resolving %s: %s", domain, e.args[1])
                return domain, []

    def _filter_ips(self, ips: list[str]) -> list[str]:
        """Filter out excluded IPs.

        Args:
            ips (list[str]): List of IPs to filter.
            dns (DNSResolver, optional): DNSResolver instance. Defaults to None,
            which creates a new instance.

        Returns:
            List of IPs excluding the excluded IPs.

        """
        return [ip for ip in ips if ip not in self._excluded]
