from time import sleep
from unittest import TestCase
from unittest.mock import patch

from pygeneral.print import Counter


class TestCounter(TestCase):
    """Test case for Counter.

    Attributes:
        cnt: the current count.
    """

    @patch("sys.stdout.write")
    def test_counter(self, patched_write):
        counter = Counter(goal=10)

        def assert_write(actual: str):
            assert actual == f"\r{counter.value}/10"
        patched_write.side_effect = assert_write

        for i in range(10):
            counter.value += 1


if __name__ == "__main__":
    counter = Counter(goal=10, prefix="Counting: ", suffix=" seconds")
    for i in range(10):
        counter.value += 1
        sleep(1)
