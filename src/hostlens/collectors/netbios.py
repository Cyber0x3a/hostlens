"""NetBIOS hostname collector"""

import asyncio
import socket

from hostlens.models import Evidence, Target


class NetbiosCollector:
    name = "netbios"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        hostname = await asyncio.to_thread(_query_name, target.ip, timeout * 0.8)
        if not hostname:
            return []
        return [Evidence(source=self.name, field="hostname", value=hostname, confidence=0.72)]


def _query_name(ip: str, timeout: float) -> str | None:
    from scapy.layers.netbios import (  # type: ignore[import-untyped]
        NBNSHeader,
        NBNSNodeStatusRequest,
    )

    request = NBNSHeader(NAME_TRN_ID=0x1234) / NBNSNodeStatusRequest(QUESTION_NAME=b"*")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.settimeout(timeout)
        connection.sendto(bytes(request), (ip, 137))
        try:
            data, _ = connection.recvfrom(1024)
        except TimeoutError:
            return None

    return hostname_from_response(data)


def hostname_from_response(data: bytes) -> str | None:
    from scapy.layers.netbios import (  # type: ignore[import-untyped]
        NBNSHeader,
        NBNSNodeStatusResponse,
    )

    response = NBNSHeader(data)
    if not response.haslayer(NBNSNodeStatusResponse):
        return None

    names = response[NBNSNodeStatusResponse].NODE_NAME or []
    for name in names:
        if int(name.SUFFIX) == 0 and not int(name.NAME_FLAGS) & 0x80:
            return bytes(name.NETBIOS_NAME).decode("ascii", errors="ignore").strip()

    return None
