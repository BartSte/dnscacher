import textwrap

from dnscache.enums import Output
from dnscache.ipset import IpSet
from tests.cases import ProjectTestCase


class TestIpSet(ProjectTestCase):
    def test_format(self):
        ipset = IpSet("dnscache")
        ipset.update(self.mappings.ips)
        actual = format(ipset, Output.IPSET.value)
        expected = textwrap.dedent(
            """
            add dnscache 1.2.3.4
            add dnscache 5.6.7.8
            add dnscache 9.10.11.12
            """
        ).strip()
        actual_lines = actual.splitlines()
        expected_lines = expected.splitlines()

        assert sorted(actual_lines) == sorted(expected_lines)
