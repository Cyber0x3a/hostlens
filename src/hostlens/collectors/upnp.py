"""UPnP device description collector"""

import asyncio
from urllib.parse import urlparse

import httpx

from hostlens.collectors.ssdp import query_ssdp
from hostlens.models import Evidence, Target
from hostlens.parsers.upnp import parse_upnp_description


class UpnpCollector:
    name = "upnp"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        responses = await asyncio.to_thread(query_ssdp, target.ip, timeout)
        locations = {headers.get("location") for headers in responses}
        evidence: list[Evidence] = []

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            for location in locations:
                if not location or not _belongs_to_target(location, target.ip):
                    continue

                try:
                    response = await client.get(location)
                    response.raise_for_status()
                except httpx.HTTPError:
                    continue

                evidence.extend(parse_upnp_description(response.content))

        return evidence


def _belongs_to_target(location: str, target_ip: str) -> bool:
    try:
        return urlparse(location).hostname == target_ip
    except ValueError:
        return False
