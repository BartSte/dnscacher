import random
from typing import Self, override

import requests


class Domains(set[str]):
    """A set subclass for handling domains with additional operations."""

    def update_from_url(self, url: str) -> Self:
        """Download the blocklist from the URL and update the set with domains.

        Args:
            url (str): URL to download the blocklist from.

        Returns:
            Domains: The updated set of domains.

        """
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        self.update(
            line.split()[1]
            for line in response.text.splitlines()
            if line.startswith("0.0.0.0")
        )
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
    def __sub__(self, other: Self) -> Self:
        """Return the difference between two Domains sets."""
        return type(self)(super().__sub__(other))

    @override
    def __and__(self, other: Self) -> Self:
        """Return the intersection of two Domains sets."""
        return type(self)(super().__and__(other))

    @override
    def __or__(self, other: Self) -> Self:
        """Return the union of two Domains sets."""
        return type(self)(super().__or__(other))

    @override
    def __repr__(self) -> str:
        """Return the official string representation of the Domains set."""
        return f"{type(self).__name__}({super().__repr__()})"

    @override
    def __str__(self) -> str:
        """Return the informal string representation of the Domains set."""
        return f"{type(self).__name__}({super().__str__()})"
