from time import sleep
from typing import override
from unittest import TestCase
from unittest.mock import patch

from pygeneral.print import StdoutCounter


class TestStdoutCounter(TestCase):
    """Test case for StdoutCounter.

    Attributes:
        cnt: the current count.
    """

    cnt: int

    @override
    def setUp(self):
        self.cnt = 0

    @patch("sys.stdout.write")
    def test_counter(self, patched_write):
        def assert_write(actual: str):
            assert actual == f"\r{self.cnt}/10"

        patched_write.side_effect = assert_write

        counter = StdoutCounter(goal=10)
        for i in range(10):
            self.cnt += 1
            counter.increment()


if __name__ == "__main__":
    counter = StdoutCounter(goal=10, prefix="Counting: ", suffix=" seconds")
    for i in range(10):
        counter.increment()
        sleep(1)
