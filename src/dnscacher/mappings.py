import asyncio
import logging
import pickle
from os import makedirs
from os.path import dirname
from typing import override

from dnscacher.domains import Domains
from dnscacher.enums import Output
from dnscacher.exceptions import InvalidCacheError
from dnscacher.ips import Ips
from dnscacher.resolve import Resolver


class Mappings(dict[str, list[str]]):
    """A dictionary mapping domains to a list of IPs with persistence and
    resolution.

    Attributes:
        path (str): Path to the pickled mappings file.

    """

    path: str

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
        resolver = Resolver(
            jobs=jobs, timeout=timeout, excluded=self.EXCLUDED_IPS
        )
        asyncio.run(resolver.fetch_ips(domains=domains, mappings=self))

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
