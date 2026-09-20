"""mDNS service collector"""

import asyncio
from collections.abc import Sequence

from hostlens.models import Evidence, Target

SERVICE_TYPES = (
    "_airplay._tcp.local.",
    "_raop._tcp.local.",
    "_googlecast._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_hap._tcp.local.",
    "_workstation._tcp.local.",
)


class MdnsCollector:
    name = "mdns"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        return await _browse(target.ip, timeout, SERVICE_TYPES)


async def _browse(
    target_ip: str,
    timeout: float,
    service_types: Sequence[str],
) -> list[Evidence]:
    from zeroconf import IPVersion, ServiceListener, Zeroconf  # type: ignore[import-untyped]
    from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf  # type: ignore[import-untyped]

    found: list[tuple[str, str]] = []

    class Listener(ServiceListener):
        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc
            found.append((type_, name))

        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc
            found.append((type_, name))

        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc, type_, name

    zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
    browsers = [
        AsyncServiceBrowser(zeroconf.zeroconf, service_type, Listener())
        for service_type in service_types
    ]

    try:
        await asyncio.sleep(timeout)
        return await _evidence_for_target(zeroconf, found, target_ip)
    finally:
        for browser in browsers:
            await browser.async_cancel()
        await zeroconf.async_close()


async def _evidence_for_target(
    zeroconf: object,
    found: list[tuple[str, str]],
    target_ip: str,
) -> list[Evidence]:
    evidence: list[Evidence] = []

    for service_type, name in dict.fromkeys(found):
        info = await zeroconf.async_get_service_info(service_type, name, timeout=100)  # type: ignore[attr-defined]
        if info is None or target_ip not in info.parsed_addresses():
            continue

        evidence.append(
            Evidence(
                source="mdns",
                field="service",
                value=service_type,
                confidence=0.9,
                description=f"mDNS advertises {service_type}",
                metadata={"instance": name},
            )
        )

        if info.server:
            evidence.append(
                Evidence(
                    source="mdns",
                    field="hostname",
                    value=info.server.rstrip("."),
                    confidence=0.82,
                )
            )

    return evidence
