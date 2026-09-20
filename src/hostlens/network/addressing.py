"""Network value normalization and local subnet detection"""

from __future__ import annotations

import ipaddress
import socket

import ifaddr

from hostlens.exceptions import DiscoveryError, InterfaceNotFound


def normalize_ip(value: str) -> str:
    """Validate and normalize an IPv4 or IPv6 address"""
    return str(ipaddress.ip_address(value))


def normalize_mac(value: str) -> str:
    """Normalize a MAC address to uppercase colon-separated notation"""
    compact = value.replace(":", "").replace("-", "").replace(".", "").strip()
    if len(compact) != 12 or any(
        character not in "0123456789abcdefABCDEF" for character in compact
    ):
        raise ValueError(f"Invalid MAC address: {value!r}")
    return ":".join(compact[index : index + 2] for index in range(0, 12, 2)).upper()


def local_ipv4_address(interface: str | None = None) -> str:
    """Find the preferred local IPv4 address without sending application data"""
    adapters = ifaddr.get_adapters()
    if interface:
        wanted = interface.casefold()
        for adapter in adapters:
            if wanted not in {adapter.name.casefold(), adapter.nice_name.casefold()}:
                continue
            for item in adapter.ips:
                if isinstance(item.ip, str) and not item.ip.startswith("127."):
                    return item.ip
        raise InterfaceNotFound(
            f"Network interface {interface!r} was not found or has no IPv4 address"
        )

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        try:
            connection.connect(("192.0.2.1", 9))
            address = connection.getsockname()[0]
        except OSError:
            address = socket.gethostbyname(socket.gethostname())
    if address.startswith("127."):
        raise DiscoveryError("Could not determine an active local IPv4 interface")
    return address


def local_subnet(interface: str | None = None) -> str:
    """Return the real subnet for the selected or preferred IPv4 interface"""
    address = local_ipv4_address(interface)
    for adapter in ifaddr.get_adapters():
        for item in adapter.ips:
            if item.ip == address:
                return str(ipaddress.ip_network(f"{address}/{item.network_prefix}", strict=False))
    raise DiscoveryError(f"Could not determine the subnet for {address}")


def validate_subnet(value: str) -> str:
    """Validate and normalize a CIDR range"""
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as error:
        raise DiscoveryError(f"Invalid subnet: {value!r}") from error
    if network.num_addresses > 65536:
        raise DiscoveryError("Refusing to scan more than 65,536 addresses at once")
    if network.version != 4:
        raise DiscoveryError("Active subnet scanning currently supports IPv4 only")
    return str(network)
