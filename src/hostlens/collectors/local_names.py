"""Local multicast hostname lookups"""

import asyncio
import random
import socket
import time

from hostlens.models import Evidence, Target


class LlmnrCollector:
    name = "llmnr"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        hostname = await asyncio.to_thread(
            query_ptr,
            target.ip,
            "224.0.0.252",
            5355,
            timeout * 0.8,
        )
        if not hostname:
            return []
        return [Evidence(source=self.name, field="hostname", value=hostname, confidence=0.82)]


def query_mdns_ptr(ip: str, timeout: float) -> str | None:
    return query_ptr(ip, "224.0.0.251", 5353, timeout, mdns=True)


def query_ptr(
    ip: str,
    multicast_address: str,
    port: int,
    timeout: float,
    *,
    mdns: bool = False,
) -> str | None:
    from scapy.layers.dns import DNS, DNSQR  # type: ignore[import-untyped]

    transaction_id = 0 if mdns else random.randint(1, 65535)
    reverse_name = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
    question = DNSQR(qname=reverse_name, qtype="PTR", unicastresponse=int(mdns))
    request = DNS(id=transaction_id, rd=0, qd=question)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        connection.sendto(bytes(request), (multicast_address, port))
        deadline = time.monotonic() + timeout

        while (remaining := deadline - time.monotonic()) > 0:
            connection.settimeout(remaining)
            try:
                data, source = connection.recvfrom(4096)
            except TimeoutError:
                return None
            if source[0] != ip:
                continue
            hostname = hostname_from_ptr_response(data, None if mdns else transaction_id)
            if hostname:
                return hostname
    return None


def hostname_from_ptr_response(data: bytes, transaction_id: int | None = None) -> str | None:
    from scapy.layers.dns import DNS  # type: ignore[import-untyped]

    response = DNS(data)
    if transaction_id is not None and int(response.id) != transaction_id:
        return None

    for answer in response.an or []:
        if int(answer.type) != 12:
            continue
        value = answer.rdata
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        hostname = str(value).rstrip(".")
        if hostname:
            return hostname
    return None
