from tempfile import NamedTemporaryFile
from unittest import TestCase

import requests

from dnscache import paths
from dnscache.domains import Domains


class TestDomains(TestCase):
    """Test cases for the Domains class."""

    def test_valid(self):
        """Test that update_from_url returns a set with domains."""
        domains = Domains().update_from_source(paths.debug)
        self.assertIsInstance(domains, set)
        self.assertTrue(len(domains) == 2)

    def test_invalid(self):
        """Test that update_from_url raises an error for an invalid URL."""
        with self.assertRaises(requests.exceptions.ConnectionError):
            Domains().update_from_source("https://notexisting_123abc.com")

    def test_not_domains_file(self):
        """Test that update_from_url returns an empty set when no valid domains
        are found."""
        with NamedTemporaryFile() as file:
            x = Domains().update_from_source(file.name)
            self.assertEqual(x, set())

    def test_operators(self):
        """Test set operators on Domains."""
        a = Domains({"a", "b", "c"})
        b = Domains({"b", "c", "d"})
        minus = a - b
        amp = a & b
        bar = a | b

        self.assertEqual(minus, {"a"})
        self.assertEqual(amp, {"b", "c"})
        self.assertEqual(bar, {"a", "b", "c", "d"})

        for x in [minus, amp, bar]:
            self.assertIsInstance(x, Domains)

    def test_empty(self):
        """Test that an empty Domains set returns an empty subset."""
        domains = Domains(set())
        subset = domains.make_random_subset(100)
        self.assertEqual(subset, set())

    def test_all(self):
        """Test that 100% subset returns the entire set."""
        domains = Domains({"a", "b", "c"})
        subset = domains.make_random_subset(100)
        self.assertEqual(subset, domains)

    def test_half(self):
        """Test that a 67% subset of three items returns two items."""
        domains = Domains({"a", "b", "c"})
        subset = domains.make_random_subset(67)
        self.assertTrue(subset.issubset(domains))
        self.assertEqual(len(subset), 2, f"len: {len(subset)}")

    def test_large(self):
        """Test that a 50% subset of 100,000 items returns exactly 50,000
        items."""
        domains = Domains({f"{x}" for x in range(100000)})
        subset = domains.make_random_subset(50)
        self.assertTrue(subset.issubset(domains))
        self.assertEqual(len(subset), 50000)
