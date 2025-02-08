import asyncio
import logging
import pickle
import socket
from collections.abc import Coroutine, Generator, Iterable
from enum import Enum
from os import makedirs
from os.path import dirname
from typing import override

import aiodns

from dnscache.domains import Domains
from dnscache.enums import Output
from dnscache.exceptions import InvalidCacheError


class Mappings(dict[str, list[str]]):
    """A dictionary mapping domains to a list of IPs with persistence and
    resolution.

    Attributes:
        path (str): Path to the pickled mappings file.

    """

    path: str
    _sem: asyncio.Semaphore
    _resolver: aiodns.DNSResolver

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
    def ips(self) -> set[str]:
        """Return a set of all IPs from the mappings.

        Returns:
            set[str]: A set of IP addresses.

        """
        return set(ip for ips in self.values() for ip in ips)

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
        logging.info("Asyncio event loop starting with %s workers", jobs)
        asyncio.run(self._resolve_multiple(domains, jobs, timeout))
        logging.info("Asyncio event loop finished")

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
        for i, future in enumerate(asyncio.as_completed(tasks)):
            domain, ips = await future
            self[domain] = ips
            if i % 1000 == 0:
                logging.info("Resolved %s domains", i)
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

    def print(self, outputs: Iterable[Output]) -> str:
        """Print the mappings in a human-readable format.

        Args:
            output: The output to print.

        Returns:
            str: the output string.

        """
        output_to_mapping: dict[Enum, str] = {
            Output.DOMAINS: "\n".join(self.domains),
            Output.IPS: "\n".join(self.ips),
            Output.MAPPINGS: str(self),
        }
        result: Generator[str] = (
            output_to_mapping[output] for output in outputs
        )
        return "\n".join(result)

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
