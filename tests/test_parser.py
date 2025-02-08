import sys
from unittest import TestCase

from dnscache.parser import Parser
from dnscache.settings import Settings


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
        arguments."""
        argv: dict[str, str | int] = {
            "jobs": 10,
            "loglevel": "INFO",
            "mappings": "/tmp/mappings.txt",
            "ipset": "blocked-ips",
            "part": 50,
        }
        sys.argv = ["update-blocklist"]
        sys.argv.append("--debug")
        sys.argv.extend([f"--{k}={v}" for k, v in argv.items()])

        args = self.parser.parse_args()
        settings = Settings(**vars(args))
        for key, value in argv.items():
            self.assertEqual(getattr(settings, key), value)
