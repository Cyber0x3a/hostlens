"""Local network discovery and addressing"""

from hostlens.network.addressing import local_subnet, normalize_ip, normalize_mac
from hostlens.network.discovery import discover_targets

__all__ = ["discover_targets", "local_subnet", "normalize_ip", "normalize_mac"]
