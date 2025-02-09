import random
import re
from collections.abc import Set
from os.path import isfile
from typing import Self, override

import requests

from dnscache.enums import Output


class Domains(set[str]):
    """A set subclass for handling domains with additional operations."""

    def update_from_source(self, source: str) -> Self:
        """Update the set of domains that is downloaded from a URL or retrieved
        from a file.

        Args:
            url (str): URL to download the blocklist from.

        Returns:
            Domains: The updated set of domains.

        """
        if isfile(source):
            self.update_from_file(source)
        else:
            self.update_from_url(source)
        return self

    def update_from_file(self, path: str) -> Self:
        """Update the set of domains that is retrieved from a file.

        Args:
            path (str): Path to the file containing the domains.

        Returns:
            Domains: The updated set of domains.

        """
        with open(path) as file:
            self.update_from_str(file.read())
        return self

    def update_from_str(self, text: str):
        """Parse text into a set of domains.

        For each line, the function extracts domains using a regular expression.
        This approach supports typical `/etc/hosts` file entries as well as
        URLs.

        Args:
            text (str): Text to parse.

        Returns:
            set[str]: Set of domains.
        """
        domain_pattern: re.Pattern[str] = re.compile(
            r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,})\b"
        )

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            matches = domain_pattern.findall(line)
            for match in matches:
                if isinstance(match, str):
                    self.add(match.lower())

    def update_from_url(self, url: str) -> Self:
        """Update the set of domains that is downloaded from a URL.

        Args:
            url: URL to download the blocklist from.

        Returns:
            the updated set of domains.
        """
        response: requests.Response = requests.get(url)
        response.raise_for_status()
        self.update_from_str(response.text)
        return self

    def make_random_subset(self, part: int) -> Self:
        """Return a random subset of the domains based on a percentage.

        Args:
            part (int): Percentage (0-100) of domains to include in the subset.

        Returns:
            Domains: A random subset of the domains.

        """
        n: int = len(self) * part // 100
        cls: type[Self] = type(self)
        return cls(random.sample(list(self), n))

    @override
    def __sub__(self, other: Set[str | None]) -> Self:
        """Return the difference between two Domains sets."""
        return type(self)(super().__sub__(other))

    @override
    def __and__(self, other: Set[object]) -> Self:
        """Return the intersection of two Domains sets."""
        return type(self)(super().__and__(other))

    @override
    def __or__(self, other: Set[str]) -> Self:
        """Return the union of two Domains sets."""
        return type(self)(super().__or__(other))

    @override
    def __repr__(self) -> str:
        """Return the official string representation of the Domains set."""
        return f"{type(self).__name__}({super().__repr__()})"

    @override
    def __str__(self) -> str:
        """Return the informal string representation of the Domains set."""
        return "\n".join(self)

    @override
    def __format__(self, format_spec: str) -> str:
        """Return a formatted string representation of the Domains set.

        Args:
            format_spec (str): Format specification.

        Returns:
            str: Formatted string representation.

        """
        return str(self) if Output(format_spec) == Output.DOMAIN else ""
