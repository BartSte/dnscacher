import textwrap

from dnscacher.enums import Output
from dnscacher.ipset import IpSet
from tests.cases import ProjectTestCase


class TestIpSet(ProjectTestCase):
    def test_format(self):
        ipset = IpSet("dnscacher")
        ipset.update(self.mappings.ips)
        actual = format(ipset, Output.IPSET.value)
        expected = textwrap.dedent(
            """
            add dnscacher 1.2.3.4
            add dnscacher 5.6.7.8
            add dnscacher 9.10.11.12
            """
        ).strip()
        actual_lines = actual.splitlines()
        expected_lines = expected.splitlines()

        assert sorted(actual_lines) == sorted(expected_lines)
