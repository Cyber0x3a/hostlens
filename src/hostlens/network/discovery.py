"""Cross-platform target discovery"""

import asyncio
import ipaddress
import logging
import re
import subprocess
from collections.abc import AsyncIterator

from hostlens.models import Target
from hostlens.network.addressing import normalize_mac

logger = logging.getLogger(__name__)


async def discover_targets(
    subnet: str,
    interface: str | None,
    arp_timeout: float,
) -> AsyncIterator[Target]:
    """Yield unique targets from the neighbor table and ARP"""
    seen_ips: set[str] = set()
    seen_macs: set[str] = set()

    async for target in known_neighbors(subnet):
        if _is_new(target, seen_ips, seen_macs):
            yield target

    for target in await scan_arp(subnet, interface, arp_timeout):
        if _is_new(target, seen_ips, seen_macs):
            yield target


async def known_neighbors(subnet: str) -> AsyncIterator[Target]:
    """Read hosts already known to the operating system"""
    output = await asyncio.to_thread(_read_neighbor_table)
    network = ipaddress.ip_network(subnet, strict=False)

    for target in parse_neighbor_table(output):
        if ipaddress.ip_address(target.ip) in network:
            yield target


async def scan_arp(
    subnet: str,
    interface: str | None,
    timeout: float,
) -> list[Target]:
    """Send one bounded IPv4 ARP discovery request"""
    try:
        return await asyncio.to_thread(_scan_arp, subnet, interface, timeout)
    except Exception as error:
        logger.debug("ARP discovery unavailable: %s", error)
        return []


def _scan_arp(subnet: str, interface: str | None, timeout: float) -> list[Target]:
    from scapy.all import ARP, Ether, conf, srp  # type: ignore[import-untyped]

    conf.verb = 0
    answered, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
        timeout=timeout,
        iface=interface,
        retry=0,
    )

    targets: list[Target] = []
    for _, reply in answered:
        targets.append(
            Target(
                ip=reply.psrc,
                mac=normalize_mac(reply.hwsrc),
                interface=interface,
            )
        )
    return targets


def _is_new(target: Target, seen_ips: set[str], seen_macs: set[str]) -> bool:
    if target.ip in seen_ips:
        return False
    if target.mac and target.mac in seen_macs:
        return False

    seen_ips.add(target.ip)
    if target.mac:
        seen_macs.add(target.mac)
    return True


def _read_neighbor_table() -> str:
    commands = (["arp", "-a"], ["ip", "neigh", "show"])
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
                timeout=3,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

        if completed.stdout:
            return completed.stdout

    return ""


_NEIGHBOR = re.compile(
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3}).*?(?P<mac>(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2})"
)


def parse_neighbor_table(output: str) -> list[Target]:
    """Parse common Windows, Linux, and macOS neighbor table formats"""
    targets: list[Target] = []

    for match in _NEIGHBOR.finditer(output):
        try:
            target = Target(
                ip=match.group("ip"),
                mac=normalize_mac(match.group("mac")),
            )
        except ValueError:
            continue
        targets.append(target)

    return targets
