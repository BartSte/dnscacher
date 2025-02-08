class InvalidCacheError(Exception):
    """Raised when the mappings cache file is invalid."""


class IpSetError(Exception):
    """Raised when an error occurs during ipset operations."""


class SettingsError(Exception):
    """Raised when a setting is missing or invalid."""
