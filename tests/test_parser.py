import sys
from os.path import join
from unittest import TestCase

from dnscacher import paths
from dnscacher.parser import Parser
from dnscacher.settings import Settings


class TestParser(TestCase):
    """Test cases for the Parser class."""

    parser: Parser
    _argv: list[str]

    def setUp(self):
        """Set up test environment for Parser tests."""
        self.parser = Parser()
        self._argv = sys.argv.copy()

    def tearDown(self):
        """Restore sys.argv after tests."""
        sys.argv = self._argv

    def test_parse(self):
        """Test that the parser correctly parses given command-line
        arguments into a Settings object with matching attributes.

        Adding options before or after the command should not affect the
        result.
        """
        options: list[str] = [
            "--jobs=10",
            "--loglevel=INFO",
            "--mappings=/tmp/mappings.txt",
            "--ipset=foo",
            "--log=/tmp/dnscacher.log",
            "--timeout=5",
            "--output=ips,mappings",
            "--quiet",
            "--debug",
        ]

        sys.argv = ["dnscacher"]
        sys.argv.append("update")
        sys.argv.extend(options)
        self._parse_assert()

        sys.argv = ["dnscacher"]
        sys.argv.extend(options)
        sys.argv.append("update")
        self._parse_assert()

    def _parse_assert(self):
        settings = self.parser.parse_args()
        settings.part = 50  # can only be added to refresh command

        expected = Settings(
            jobs=10,
            command="update",
            loglevel="INFO",
            mappings="/tmp/mappings.txt",
            ipset="foo",
            log="/tmp/dnscacher.log",
            part=50,
            timeout=5,
            output=("ips", "mappings"),
            debug=True,
            quiet=True,
            source=join(paths.root, "debug.txt"),
        )
        for key in expected.as_dict():
            self.assertEqual(
                getattr(expected, key),
                getattr(settings, key),
                msg=f"Failed on key: {key}",
            )
