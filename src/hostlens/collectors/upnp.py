"""Shared SSDP and UPnP discovery"""

import asyncio
import socket
import time
from urllib.parse import urlparse

import httpx

from hostlens.models import Evidence, Target
from hostlens.parsers.ssdp import parse_ssdp_headers
from hostlens.parsers.upnp import parse_upnp_description


class UpnpCollector:
    name = "upnp"

    def __init__(self) -> None:
        self._scan: asyncio.Task[dict[str, list[Evidence]]] | None = None
        self._started = 0.0

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        if self._scan is None or time.monotonic() - self._started > 30:
            self._started = time.monotonic()
            self._scan = asyncio.create_task(_discover(timeout))
        return list((await asyncio.shield(self._scan)).get(target.ip, []))


async def _discover(timeout: float) -> dict[str, list[Evidence]]:
    discovery_time = min(1.0, timeout * 0.45)
    responses = await asyncio.to_thread(query_ssdp, discovery_time)
    results: dict[str, list[Evidence]] = {}
    locations: set[tuple[str, str]] = set()

    for ip, headers in responses:
        evidence = results.setdefault(ip, [])
        location = headers.get("location")
        if location and _belongs_to_target(location, ip):
            locations.add((ip, location))
            evidence.append(
                Evidence(source="ssdp", field="upnp_location", value=location, confidence=0.95)
            )

        server = headers.get("server")
        if server:
            evidence.append(
                Evidence(
                    source="ssdp",
                    field="server",
                    value=server,
                    confidence=0.75,
                    description=f"SSDP reports server {server}",
                )
            )

    http_timeout = max(0.2, timeout * 0.35)
    unique_locations = sorted(locations)
    async with httpx.AsyncClient(timeout=http_timeout, follow_redirects=False) as client:
        descriptions = await asyncio.gather(
            *(_fetch_description(client, location) for _, location in unique_locations)
        )

    for (ip, _), evidence in zip(unique_locations, descriptions, strict=True):
        results.setdefault(ip, []).extend(evidence)
    return results


def query_ssdp(timeout: float) -> list[tuple[str, dict[str, str]]]:
    message = (
        b"M-SEARCH * HTTP/1.1\r\n"
        b"HOST: 239.255.255.250:1900\r\n"
        b'MAN: "ssdp:discover"\r\n'
        b"MX: 1\r\n"
        b"ST: ssdp:all\r\n\r\n"
    )
    responses: list[tuple[str, dict[str, str]]] = []
    deadline = time.monotonic() + timeout

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        connection.sendto(message, ("239.255.255.250", 1900))

        while (remaining := deadline - time.monotonic()) > 0:
            connection.settimeout(remaining)
            try:
                data, source = connection.recvfrom(65535)
            except TimeoutError:
                break
            responses.append((source[0], parse_ssdp_headers(data)))

    return responses


async def _fetch_description(client: httpx.AsyncClient, location: str) -> list[Evidence]:
    try:
        response = await client.get(location)
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    return parse_upnp_description(response.content)


def _belongs_to_target(location: str, target_ip: str) -> bool:
    try:
        return urlparse(location).hostname == target_ip
    except ValueError:
        return False
