"""Fast hostname and manufacturer collectors"""

import asyncio
import socket

from hostlens.models import Evidence, Target


class HostnameCollector:
    name = "hostname"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(socket.gethostbyaddr, target.ip),
                timeout=timeout,
            )
        except (TimeoutError, OSError):
            return []

        hostname = result[0].rstrip(".")
        return [
            Evidence(
                source=self.name,
                field="hostname",
                value=hostname,
                confidence=0.75,
                description=f"Reverse DNS reports hostname {hostname}",
            )
        ]


class OuiCollector:
    name = "oui"

    def __init__(self) -> None:
        self.parser: object | None = None

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        del timeout
        if not target.mac:
            return []

        manufacturer = await asyncio.to_thread(self._lookup, target.mac)
        if not manufacturer:
            return []

        return [
            Evidence(
                source=self.name,
                field="manufacturer",
                value=manufacturer,
                confidence=0.78,
                description=f"MAC prefix matches {manufacturer}",
            )
        ]

    def _lookup(self, mac: str) -> str | None:
        from manuf import manuf  # type: ignore[import-untyped]

        if self.parser is None:
            self.parser = manuf.MacParser(update=False)

        manufacturer = self.parser.get_manuf_long(mac) or self.parser.get_manuf(mac)  # type: ignore[attr-defined]
        return str(manufacturer).strip() if manufacturer else None
