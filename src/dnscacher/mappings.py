import asyncio
import logging
import pickle
import socket
from collections.abc import Coroutine
from os import makedirs
from os.path import dirname
from typing import override

import aiodns

from dnscacher.domains import Domains
from dnscacher.enums import Output
from dnscacher.exceptions import InvalidCacheError
from dnscacher.helpers import StdoutCounter
from dnscacher.ips import Ips


class Mappings(dict[str, list[str]]):
    """A dictionary mapping domains to a list of IPs with persistence and
    resolution.

    Attributes:
        path (str): Path to the pickled mappings file.

    """

    path: str
    _sem: asyncio.Semaphore
    _resolver: aiodns.DNSResolver

    EXCLUDED_IPS: set[str] = {"0.0.0.0", "127.0.0.1"}

    def __init__(self, path: str):
        """Initialize the Mappings object.

        Args:
            path (str): File path to load/save the domain→IP mappings.

        """
        super().__init__()
        self.path = path

    @property
    def domains(self) -> Domains:
        """Return a Domains set containing all mapped domains.

        Returns:
            Domains: A set of domains.

        """
        return Domains(self.keys())

    @property
    def ips(self) -> Ips:
        """Return a set of all IPs from the mappings.

        Returns:
            set[str]: A set of IP addresses.

        """
        return Ips(ip for ips in self.values() for ip in ips)

    def load(self):
        """Load domain→IP mappings from a pickle file.

        Raises:
            InvalidCacheError: If the mappings file is invalid.

        """
        try:
            with open(self.path, "rb") as f:
                self.update(pickle.load(f))
        except FileNotFoundError:
            logging.info("No mappings file found at %s", self.path)
        except pickle.UnpicklingError as e:
            raise InvalidCacheError(
                f"Invalid mappings file at {self.path}"
            ) from e
        except Exception as e:
            raise InvalidCacheError(
                f"Error loading mappings file at {self.path}"
            ) from e
        else:
            logging.info("Loaded %s mappings from %s", len(self), self.path)

    def save(self):
        """Save the current domain→IP mappings to a pickle file.

        Raises:
            InvalidCacheError: If saving fails.

        """
        makedirs(dirname(self.path), exist_ok=True)
        logging.info("Saving %s mappings to %s", len(self), self.path)
        try:
            with open(self.path, "wb") as f:
                pickle.dump(dict(self), f)
        except Exception as e:
            raise InvalidCacheError(
                f"Error saving mappings file at {self.path}"
            ) from e

    def update_by_resolving(
        self, domains: Domains, jobs: int = 10000, timeout: int = 5
    ):
        """Update mappings by asynchronously resolving a set of domains.

        Args:
            domains (Domains): Set of domains to resolve.
            jobs (int, optional): Number of concurrent workers. Defaults to
            10000.
            timeout (int, optional): Timeout in seconds for each resolution.
            Defaults to 5.

        """
        logging.debug("Asyncio event loop starting with %s workers", jobs)
        asyncio.run(self._resolve_multiple(domains, jobs, timeout))
        logging.debug("Asyncio event loop finished")

    async def _resolve_multiple(
        self, domains: Domains, jobs: int = 10000, timeout: int = 5
    ):
        """Resolve multiple domains concurrently.

        Args:
            domains (Domains): Set of domains to resolve.
            jobs (int, optional): Maximum number of concurrent resolutions.
            timeout (int, optional): Timeout for each resolution.

        """
        self._sem = asyncio.Semaphore(jobs)
        self._resolver = aiodns.DNSResolver()
        tasks: list[Coroutine[None, None, tuple[str, list[str]]]] = [
            self._resolve(domain, timeout) for domain in domains
        ]
        logging.info("Resolving %s domains async", len(tasks))

        stdout_counter = StdoutCounter(
            goal=len(tasks),
            prefix="Resolving: ",
            suffix=f" domains with {jobs} workers",
        )
        for i, future in enumerate(asyncio.as_completed(tasks)):
            domain, ips = await future
            ips = self._filter_ips(ips)
            self[domain] = ips
            stdout_counter.increment()
        logging.info("Resolved %s domains", len(tasks))

    async def _resolve(
        self, domain: str, timeout: int = 5
    ) -> tuple[str, list[str]]:
        """Asynchronously resolve a single domain to its IPv4 addresses.

        Args:
            domain (str): The domain to resolve.
            timeout (int, optional): Timeout for the resolution. Defaults to 5.

        Returns:
            A tuple containing the domain and a list of resolved IPs.

        """
        async with self._sem:
            try:
                result = await asyncio.wait_for(
                    self._resolver.gethostbyname(domain, socket.AF_INET),
                    timeout=timeout,
                )
                return domain, result.addresses
            except asyncio.TimeoutError:
                logging.debug("Timeout resolving %s", domain)
                return domain, []
            except aiodns.error.DNSError as e:
                logging.debug("Error resolving %s: %s", domain, e.args[1])
                return domain, []

    def _filter_ips(self, ips: list[str]) -> list[str]:
        """Filter out IPs that are in Mappings.EXCLUDED_IPS.

        Args:
            ips (list[str]): List of IP addresses.

        Returns:
            list[str]: List of filtered IP addresses.

        """
        return [ip for ip in ips if ip not in self.EXCLUDED_IPS]

    @override
    def __format__(self, format_spec: str) -> str:
        """Return a formatted string representation of the Mappings object.

        Args:
            format_spec: The format specifier based on value of the `Output`
            enum.

        Returns:
            str: A formatted string representation of the Mappings object.

        """
        return str(self) if Output(format_spec) == Output.MAPPING else ""

    @override
    def __str__(self) -> str:
        """Return a string representation of the Mappings object.

        domain ip1 ip2 ip3 ...

        Returns:
            str: A string representation of the Mappings object.

        """
        return "\n".join(
            f"{domain} {' '.join(ips)}" for domain, ips in self.items()
        )
