import sys
from argparse import ArgumentParser
from os.path import join
from unittest import TestCase

from dnscache import paths
from dnscache.parser import make_parser
from dnscache.settings import Settings


class TestParser(TestCase):
    """Test cases for the Parser class."""

    parser: ArgumentParser
    _argv: list[str]

    def setUp(self):
        """Set up test environment for Parser tests."""
        self.parser = make_parser()
        self._argv = sys.argv.copy()

    def tearDown(self):
        """Restore sys.argv after tests."""
        sys.argv = self._argv

    def test_parse(self):
        """Test that the parser correctly parses given command-line
        arguments into a Settings object with matching attributes."""
        options: list[str] = [
            "--jobs=10",
            "--loglevel=INFO",
            "--mappings=/tmp/mappings.txt",
            "--ipset=blocked-ips",
            "--part=50",
            "--log=/tmp/dnscache.log",
            "--timeout=5",
            "--output",
            "ips",
            "mappings",
            "--debug",
        ]
        sys.argv = ["update-blocklist"]
        sys.argv.extend(options)
        sys.argv.append("resolve")

        args = self.parser.parse_args()
        kwargs = {k: v for k, v in vars(args).items() if v}
        settings = Settings(**kwargs)

        # Assert args and settings have the same values.
        for key in settings.as_dict():
            self.assertEqual(
                getattr(settings, key),
                getattr(args, key),
                msg=f"Failed on key: {key}",
            )

        # Assert the settings object has the expected values.
        expected = Settings(
            jobs=10,
            command="resolve",
            loglevel="INFO",
            mappings="/tmp/mappings.txt",
            ipset="blocked-ips",
            part=50,
            log="/tmp/dnscache.log",
            timeout=5,
            output=("ips", "mappings"),
            debug=True,
            source=join(paths.root, "debug.txt"),
        )
        for key in expected.as_dict():
            self.assertEqual(
                getattr(expected, key),
                getattr(settings, key),
                msg=f"Failed on key: {key}",
            )
