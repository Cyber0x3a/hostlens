"""Small curated TCP service collector"""

import asyncio

from hostlens.models import Evidence, Service, Target

PORTS = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    445: "SMB",
    554: "RTSP",
    9100: "Printer",
}


class ServiceCollector:
    name = "services"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        checks = [_check_port(target.ip, port, timeout) for port in PORTS]
        services = [service for service in await asyncio.gather(*checks) if service]
        if not services:
            return []

        return [
            Evidence(
                source=self.name,
                field="services",
                value=[service.model_dump_json() for service in services],
                confidence=0.9,
                description="Selected TCP services responded",
            )
        ]


async def _check_port(ip: str, port: int, timeout: float) -> Service | None:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), min(timeout, 1.0))
    except (TimeoutError, OSError):
        return None

    writer.close()
    await writer.wait_closed()
    return Service(name=PORTS[port], protocol="tcp", port=port)
