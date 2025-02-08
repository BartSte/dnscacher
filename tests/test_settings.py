from os.path import dirname
from unittest import TestCase

from dnscache.settings import Settings


class TestSettings(TestCase):
    """Test cases for the Settings class."""

    def test_makedirs(self):
        """Test that makedirs creates the required directory for mappings."""
        import os
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdirname:
            settings = Settings(mappings=f"{tmpdirname}/subdir/mappings_file")
            settings.makedirs()
            self.assertTrue(os.path.isdir(dirname(settings.mappings)))
