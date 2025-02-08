import pickle
from contextlib import suppress
from os import remove
from unittest import TestCase

from dnscache.domains import Domains
from dnscache.mappings import InvalidCacheError, Mappings
from dnscache.settings import Settings


class TestMappings(TestCase):
    """Test cases for the Mappings class."""

    settings: Settings
    mappings: Mappings

    def setUp(self) -> None:
        """Set up test environment for Mappings tests."""
        self.settings = Settings(mappings="/tmp/mappings", debug=True)
        self.mappings = Mappings(path=self.settings.mappings)
        self.mappings.update(
            {
                "example.com": ["1.2.3.4"],
                "example.org": ["5.6.7.8", "9.10.11.12"],
            }
        )

    def tearDown(self) -> None:
        """Clean up after Mappings tests."""
        with suppress(FileNotFoundError):
            remove(self.settings.mappings)

    def test_valid(self):
        """Test saving and loading valid mappings."""
        self.mappings.save()
        result = Mappings(self.settings.mappings)
        result.load()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, self.mappings)

    def test_empty(self):
        """Test loading when mappings file is empty or missing."""
        result = Mappings("/tmp/nonexistent_mappings")
        result.load()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_invalid(self):
        """Test that loading an invalid mappings file raises
        InvalidCacheError."""
        with open(self.settings.mappings, "wb") as f:
            pickle.dump({"invalid", "object"}, f)
        result = Mappings(self.settings.mappings)
        with self.assertRaises(InvalidCacheError):
            result.load()

    def test_update_by_resolving(self):
        """Test that update_by_resolving correctly adds new mappings."""
        domains = Domains({"example.net", "example.nl"})
        self.mappings.update_by_resolving(domains)
        # Expect at least 4 mappings: the two originally set plus two new ones.
        self.assertGreaterEqual(len(self.mappings), 4)
        print(self.mappings)
