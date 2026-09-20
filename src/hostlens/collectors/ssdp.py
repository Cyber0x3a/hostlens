"""SSDP discovery collector"""

import asyncio
import socket

from hostlens.models import Evidence, Target
from hostlens.parsers.ssdp import parse_ssdp_headers


class SsdpCollector:
    name = "ssdp"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        responses = await asyncio.to_thread(query_ssdp, target.ip, timeout)
        evidence: list[Evidence] = []

        for headers in responses:
            location = headers.get("location")
            if location:
                evidence.append(
                    Evidence(
                        source=self.name,
                        field="upnp_location",
                        value=location,
                        confidence=0.95,
                    )
                )

            server = headers.get("server")
            if server:
                evidence.append(
                    Evidence(
                        source=self.name,
                        field="server",
                        value=server,
                        confidence=0.75,
                        description=f"SSDP reports server {server}",
                    )
                )

        return evidence


def query_ssdp(ip: str, timeout: float) -> list[dict[str, str]]:
    message = (
        b"M-SEARCH * HTTP/1.1\r\n"
        b"HOST: 239.255.255.250:1900\r\n"
        b'MAN: "ssdp:discover"\r\n'
        b"MX: 1\r\n"
        b"ST: ssdp:all\r\n\r\n"
    )
    responses: list[dict[str, str]] = []

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.settimeout(timeout)
        connection.sendto(message, (ip, 1900))

        while True:
            try:
                data, _ = connection.recvfrom(65535)
            except TimeoutError:
                break
            responses.append(parse_ssdp_headers(data))

    return responses
