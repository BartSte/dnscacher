from enum import Enum


class Command(Enum):
    """Command: Command to execute."""

    RESOLVE = "resolve"
    RETRIEVE = "retrieve"


class Output(Enum):
    IP = "ips"
    DOMAIN = "domains"
    MAPPING = "mappings"
    IPSET = "ipset"

    @classmethod
    def multiple(cls, values: str | list[str]) -> tuple["Output", ...]:
        """Return a list of Output values from a comma-separated string.

        Args:
            value (str): Comma-separated string of Output values.

        Returns:
            list[Self]: List of Output values.

        """
        if isinstance(values, str):
            values = [values]
        return tuple(cls(v) for v in values)
