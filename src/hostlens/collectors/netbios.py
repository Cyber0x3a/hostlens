"""NetBIOS hostname collector"""

import asyncio
import socket
import struct

from hostlens.models import Evidence, Target


class NetbiosCollector:
    name = "netbios"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        hostname = await asyncio.to_thread(_query_name, target.ip, timeout)
        if not hostname:
            return []
        return [Evidence(source=self.name, field="hostname", value=hostname, confidence=0.72)]


def _query_name(ip: str, timeout: float) -> str | None:
    transaction = b"\x12\x34"
    header = transaction + b"\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    wildcard = b" CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01"

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.settimeout(timeout)
        connection.sendto(header + wildcard, (ip, 137))
        try:
            data, _ = connection.recvfrom(1024)
        except TimeoutError:
            return None

    if len(data) < 57:
        return None

    count = data[56]
    offset = 57
    for _ in range(count):
        if offset + 18 > len(data):
            break

        hostname = data[offset : offset + 15].decode("ascii", errors="ignore").strip()
        suffix = data[offset + 15]
        flags = struct.unpack("!H", data[offset + 16 : offset + 18])[0]
        if suffix == 0 and not flags & 0x8000:
            return hostname
        offset += 18

    return None
