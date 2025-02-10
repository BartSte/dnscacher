import re
import textwrap

from dnscacher import formatter
from dnscacher.enums import Output
from tests.cases import ProjectTestCase


class TestFormatter(ProjectTestCase):
    """Test cases for the formatter module."""

    def test_product(self):
        """Test that the product function returns the expected output.

        The order of the output is not guaranteed but the sections are, i.e.,
        ips, domains, and mappings, respectively.
        """
        outputs: tuple[str, ...] = tuple(x.value for x in Output)
        expected: str = textwrap.dedent(
            """
            1.2.3.4
            5.6.7.8
            9.10.11.12
            example.com
            example.org
            example.com 1.2.3.4
            example.org 5.6.7.8 9.10.11.12
            """
        ).strip()
        actual: str = formatter.product(
            [self.mappings, self.mappings.ips, self.mappings.domains], outputs
        )

        actual_lines = actual.splitlines()
        expected_lines = expected.splitlines()

        assert sorted(actual_lines) == sorted(expected_lines)

        # first 3 lines are ips
        for line in actual_lines[:3]:
            assert re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line)

        # next 2 lines are domains
        for line in actual_lines[3:5]:
            assert re.match(r"\w+\.\w+", line)
