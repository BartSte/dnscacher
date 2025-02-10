from typing import override

from dnscacher.enums import Output


class IpSet(set[str]):
    """A helper class for managing ipset operations.

    Attributes:
        name (str): The name of the ipset.

    """

    name: str

    def __init__(self, name: str):
        """Initialize the IpSet.

        Args:
            name (str): The name of the ipset.

        """
        self.name = name

    @override
    def __format__(self, format_spec: str) -> str:
        """Return the name of the ipset."""
        return str(self) if Output(format_spec) == Output.IPSET else ""

    @override
    def __str__(self) -> str:
        """Return the name of the ipset."""
        return "\n".join(f"add {self.name} {ip}" for ip in self)
