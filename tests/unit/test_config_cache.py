import pytest

from hostlens.cache import MemoryCache
from hostlens.config import ScanMode, parse_scan_mode, validate_options
from hostlens.exceptions import ConfigurationError


def test_scan_mode_accepts_strings() -> None:
    assert parse_scan_mode("FAST") is ScanMode.FAST


def test_cloud_requires_an_api_key() -> None:
    with pytest.raises(ConfigurationError):
        validate_options(timeout=3, concurrency=64, cloud=True, api_key=None)


def test_memory_cache_can_clear() -> None:
    cache: MemoryCache[str] = MemoryCache()
    cache.set("key", "value")
    assert cache.get("key") == "value"
    cache.clear()
    assert cache.get("key") is None
