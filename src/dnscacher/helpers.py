import os
import sys


def is_root() -> bool:
    """Check if the script is run as root.

    Returns:
        True if the script is run as root, False otherwise.
    """
    try:
        if os.name == "nt":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.getuid() == 0
    except Exception:
        return False


class StdoutCounter:
    """
    A simple counter that writes progress to standard output on a single line.

    Attributes:
        index: The current count.
        goal: The optional goal or upper limit for the counter.
        prefix: An optional prefix string to display before the counter.
        suffix: An optional suffix string to display after the counter.
    """

    index: int
    goal: int | None
    prefix: str
    suffix: str

    def __init__(
        self,
        *,
        index: int = 0,
        goal: int | None = None,
        prefix: str = "",
        suffix: str = "",
    ) -> None:
        """
        Initialize the StdoutCounter.

        Args:
            index: The starting count (default 0).
            goal: The optional end goal for the counter.
            prefix: Text to display before the count.
            suffix: Text to display after the count.
        """
        self.index = index
        self.goal = goal
        self.prefix = prefix
        self.suffix = suffix

    def increment(self, value: int = 1) -> None:
        """
        Increase the counter by a given value and print the updated progress.

        Args:
            value: The amount by which to increment the counter (default 1).
        """
        self.index += value
        message = self.make_message()
        sys.stdout.write(message)
        sys.stdout.flush()

    def make_message(self) -> str:
        """
        Build the progress message for display on stdout.

        Returns:
            A string containing the prefix, current count, and suffix
            (including a carriage return at the beginning).
        """
        count_str = self.make_count()
        return f"\r{self.prefix}{count_str}{self.suffix}"

    def make_count(self) -> str:
        """
        Create a human-readable representation of the current count
        and goal (if provided).

        Returns:
            A string with either just the current count, or `current/goal`.
        """
        if self.goal is None:
            return str(self.index)
        return f"{self.index}/{self.goal}"
