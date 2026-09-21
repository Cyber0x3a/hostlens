"""Shared mDNS and DNS-SD discovery"""

import asyncio
import time
from collections.abc import Mapping

from hostlens.collectors.local_names import query_mdns_ptr
from hostlens.models import Evidence, Target

FALLBACK_SERVICE_TYPES = (
    "_airplay._tcp.local.",
    "_device-info._tcp.local.",
    "_googlecast._tcp.local.",
    "_hap._tcp.local.",
    "_http._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_raop._tcp.local.",
    "_smb._tcp.local.",
    "_workstation._tcp.local.",
)


class MdnsCollector:
    name = "mdns"

    def __init__(self) -> None:
        self._scan: asyncio.Task[dict[str, list[Evidence]]] | None = None
        self._started = 0.0

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        if self._scan is None or time.monotonic() - self._started > 30:
            self._started = time.monotonic()
            self._scan = asyncio.create_task(_discover_services(timeout * 0.6))

        evidence = list((await asyncio.shield(self._scan)).get(target.ip, []))
        if not any(item.field == "hostname" for item in evidence):
            hostname = await asyncio.to_thread(query_mdns_ptr, target.ip, max(0.1, timeout * 0.25))
            if hostname:
                evidence.append(
                    Evidence(source=self.name, field="hostname", value=hostname, confidence=0.88)
                )
        return evidence


async def _discover_services(timeout: float) -> dict[str, list[Evidence]]:
    from zeroconf import IPVersion, ServiceListener, Zeroconf  # type: ignore[import-untyped]
    from zeroconf.asyncio import (  # type: ignore[import-untyped]
        AsyncServiceBrowser,
        AsyncZeroconf,
        AsyncZeroconfServiceTypes,
    )

    found: set[tuple[str, str]] = set()

    class Listener(ServiceListener):
        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc
            found.add((type_, name))

        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc
            found.add((type_, name))

        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            del zc, type_, name

    zeroconf = AsyncZeroconf(ip_version=IPVersion.V4Only)
    browser = None

    try:
        enumeration_time = min(0.75, timeout * 0.4)
        advertised = await AsyncZeroconfServiceTypes.async_find(
            aiozc=zeroconf,
            timeout=enumeration_time,
        )
        service_types = sorted(set(FALLBACK_SERVICE_TYPES) | set(advertised))
        browser = AsyncServiceBrowser(zeroconf.zeroconf, service_types, Listener())
        await asyncio.sleep(max(0.1, timeout - enumeration_time - 0.25))

        services = list(found)
        details = await asyncio.gather(
            *(zeroconf.async_get_service_info(type_, name, timeout=250) for type_, name in services)
        )

        results: dict[str, list[Evidence]] = {}
        for (service_type, name), info in zip(services, details, strict=True):
            if info is None:
                continue
            evidence = service_evidence(service_type, name, info.server, info.properties)
            for address in info.parsed_addresses():
                results.setdefault(address, []).extend(evidence)
        return results
    finally:
        if browser is not None:
            await browser.async_cancel()
        await zeroconf.async_close()


def service_evidence(
    service_type: str,
    name: str,
    server: str | None,
    properties: Mapping[bytes, bytes | None],
) -> list[Evidence]:
    evidence = [
        Evidence(
            source="mdns",
            field="service",
            value=service_type,
            confidence=0.9,
            description=f"mDNS advertises {service_type}",
            metadata={"instance": name},
        )
    ]

    if server:
        evidence.append(
            Evidence(
                source="mdns",
                field="hostname",
                value=server.rstrip("."),
                confidence=0.9,
            )
        )

    friendly_name = _property(properties, "fn", "name") or name.removesuffix(f".{service_type}")
    if friendly_name:
        evidence.append(
            Evidence(
                source="mdns",
                field="friendly_name",
                value=friendly_name,
                confidence=0.8,
            )
        )

    model = _property(properties, "md", "model", "ty")
    if model:
        evidence.append(Evidence(source="mdns", field="model", value=model, confidence=0.8))

    manufacturer = _property(properties, "manufacturer", "mf")
    if manufacturer:
        evidence.append(
            Evidence(source="mdns", field="manufacturer", value=manufacturer, confidence=0.8)
        )

    return evidence


def _property(properties: Mapping[bytes, bytes | None], *names: str) -> str | None:
    lowered = {key.decode(errors="ignore").lower(): value for key, value in properties.items()}
    for name in names:
        value = lowered.get(name)
        if value:
            return value.decode(errors="ignore").strip() or None
    return None
