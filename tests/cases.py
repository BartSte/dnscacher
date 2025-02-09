from typing import override
from unittest import TestCase

from dnscache.mappings import Mappings
from dnscache.settings import Settings


class ProjectTestCase(TestCase):
    settings: Settings
    mappings: Mappings

    @override
    def setUp(self):
        """Set up test environment for formatter tests."""
        self.settings = Settings(debug=True)
        self.mappings = Mappings(path=self.settings.mappings)
        self.mappings.update(
            {
                "example.com": ["1.2.3.4"],
                "example.org": ["5.6.7.8", "9.10.11.12"],
            }
        )
