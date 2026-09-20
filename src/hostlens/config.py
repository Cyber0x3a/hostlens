"""Scan modes and their defaults"""

from enum import StrEnum

from hostlens.exceptions import ConfigurationError


class ScanMode(StrEnum):
    FAST = "fast"
    NORMAL = "normal"
    DEEP = "deep"
    PASSIVE = "passive"


_TIMEOUTS = {
    ScanMode.FAST: 0.8,
    ScanMode.NORMAL: 2.5,
    ScanMode.DEEP: 5.0,
    ScanMode.PASSIVE: 30.0,
}

_CONCURRENCY = {
    ScanMode.FAST: 64,
    ScanMode.NORMAL: 48,
    ScanMode.DEEP: 24,
    ScanMode.PASSIVE: 16,
}

_COLLECTORS = {
    ScanMode.FAST: ("hostname", "oui"),
    ScanMode.NORMAL: ("hostname", "oui", "mdns", "ssdp", "upnp"),
    ScanMode.DEEP: (
        "hostname",
        "oui",
        "mdns",
        "ssdp",
        "upnp",
        "netbios",
        "services",
    ),
    ScanMode.PASSIVE: ("oui",),
}


def parse_scan_mode(mode: ScanMode | str) -> ScanMode:
    try:
        return ScanMode(str(mode).lower())
    except ValueError as error:
        choices = ", ".join(item.value for item in ScanMode)
        raise ConfigurationError(f"Unknown scan mode {mode!r}, choose from {choices}") from error


def scan_timeout(mode: ScanMode) -> float:
    return _TIMEOUTS[mode]


def scan_concurrency(mode: ScanMode) -> int:
    return _CONCURRENCY[mode]


def scan_collectors(mode: ScanMode) -> tuple[str, ...]:
    return _COLLECTORS[mode]


def validate_options(timeout: float, concurrency: int, cloud: bool, api_key: str | None) -> None:
    if timeout <= 0:
        raise ConfigurationError("timeout must be greater than zero")
    if concurrency < 1:
        raise ConfigurationError("concurrency must be at least one")
    if cloud and not api_key:
        raise ConfigurationError("cloud=True requires a Fingerbank API key")
