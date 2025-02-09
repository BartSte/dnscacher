from typing import override

from dnscache.enums import Output


class Ips(set[str]):
    """A set of IP addresses with persistence and resolution.

    Attributes:
        path (str): Path to the pickled IPs file.

    """

    @override
    def __format__(self, format_spec: str) -> str:
        """Return a formatted string representation of the IPs.

        Args:
            format_spec (str): Format specification.

        Returns:
            str: Formatted string representation.

        """
        return str(self) if Output(format_spec) == Output.IP else ""

    @override
    def __repr__(self) -> str:
        """Return the official string representation of the IPs set."""
        return "\n".join(self)
