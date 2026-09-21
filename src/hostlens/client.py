"""The public async HostLens client"""

import asyncio
import ipaddress
import logging
import time
from collections.abc import AsyncIterator, Sequence

from hostlens.cache import MemoryCache
from hostlens.collectors import (
    Collector,
    HostnameCollector,
    LlmnrCollector,
    MdnsCollector,
    NetbiosCollector,
    OuiCollector,
    ServiceCollector,
    UpnpCollector,
    collect_evidence,
)
from hostlens.config import (
    ScanMode,
    parse_scan_mode,
    scan_collectors,
    scan_concurrency,
    scan_timeout,
    validate_options,
)
from hostlens.identity.fingerbank import FingerbankClient
from hostlens.identity.fingerprints import apply_local_rules
from hostlens.identity.fusion import build_profile
from hostlens.models import (
    DeviceFound,
    DeviceIdentified,
    DeviceProfile,
    DeviceUpdated,
    ScanCompleted,
    ScanEvent,
    ScanResult,
    ScanSummary,
    Target,
)
from hostlens.network.addressing import local_subnet, normalize_ip, validate_subnet
from hostlens.network.discovery import discover_targets, known_neighbors

logger = logging.getLogger(__name__)


def _built_in_collectors() -> tuple[Collector, ...]:
    return (
        HostnameCollector(),
        OuiCollector(),
        MdnsCollector(),
        LlmnrCollector(),
        UpnpCollector(),
        NetbiosCollector(),
        ServiceCollector(),
    )


class HostLens:
    """Discover and identify devices through one async API"""

    def __init__(
        self,
        *,
        interface: str | None = None,
        timeout: float = 3.0,
        concurrency: int = 64,
        cloud: bool = False,
        fingerbank_api_key: str | None = None,
        collectors: Sequence[Collector] | None = None,
    ) -> None:
        validate_options(timeout, concurrency, cloud, fingerbank_api_key)

        self.interface = interface
        self.timeout = timeout
        self.concurrency = concurrency
        self.cache: MemoryCache[DeviceProfile] = MemoryCache(ttl=300)

        available = collectors if collectors is not None else _built_in_collectors()
        self.collectors = {collector.name: collector for collector in available}

        self.fingerbank = None
        if cloud and fingerbank_api_key:
            self.fingerbank = FingerbankClient(fingerbank_api_key, timeout)

    async def identify(
        self,
        target: str,
        *,
        mode: ScanMode | str = ScanMode.NORMAL,
    ) -> DeviceProfile:
        """Identify one IP address"""
        return await self.scan_host(target, mode=mode)

    async def scan_host(
        self,
        target: str,
        *,
        mode: ScanMode | str = ScanMode.NORMAL,
    ) -> DeviceProfile:
        """Scan and identify one host"""
        ip = normalize_ip(target)
        cached = self.cache.get(ip)
        if cached:
            return cached

        resolved_target = await self._find_neighbor(ip)
        device = await self._identify_target(resolved_target, parse_scan_mode(mode))
        self.cache.set(ip, device)
        return device

    async def scan_hosts(
        self,
        targets: Sequence[str],
        *,
        mode: ScanMode | str = ScanMode.NORMAL,
    ) -> list[DeviceProfile]:
        """Identify several hosts with bounded concurrency"""
        scan_mode = parse_scan_mode(mode)
        limit = min(self.concurrency, scan_concurrency(scan_mode))
        semaphore = asyncio.Semaphore(limit)

        async def scan_one(target: str) -> DeviceProfile:
            async with semaphore:
                return await self.scan_host(target, mode=scan_mode)

        tasks = [scan_one(target) for target in targets]
        return list(await asyncio.gather(*tasks))

    async def scan_network(
        self,
        subnet: str | None = None,
        *,
        mode: ScanMode | str = ScanMode.NORMAL,
        return_result: bool = False,
    ) -> list[DeviceProfile] | ScanResult:
        """Discover and identify devices on one subnet"""
        devices: dict[str, DeviceProfile] = {}
        summary = None

        async for event in self.scan_stream(subnet, mode=mode):
            if isinstance(event, (DeviceFound, DeviceUpdated, DeviceIdentified)):
                key = event.device.mac or event.device.ip
                devices[key] = event.device
            if isinstance(event, ScanCompleted):
                summary = event.summary

        found = list(devices.values())
        if return_result:
            if summary is None:
                raise RuntimeError("Scan finished without a summary")
            return ScanResult(devices=found, summary=summary)
        return found

    async def discover(self, subnet: str | None = None) -> list[DeviceProfile]:
        """Run a fast network scan"""
        result = await self.scan_network(subnet, mode=ScanMode.FAST)
        if isinstance(result, ScanResult):
            return result.devices
        return result

    async def scan(self, subnet: str | None = None) -> AsyncIterator[ScanEvent]:
        """Stream a normal network scan"""
        async for event in self.scan_stream(subnet):
            yield event

    async def scan_stream(
        self,
        subnet: str | None = None,
        *,
        mode: ScanMode | str = ScanMode.NORMAL,
    ) -> AsyncIterator[ScanEvent]:
        """Yield devices early and enrich them as the scan continues"""
        started = time.monotonic()
        scan_mode = parse_scan_mode(mode)
        if scan_mode is ScanMode.PASSIVE:
            raise ValueError("Use watch_network for passive observation")

        network = self._network(subnet)
        targets: list[Target] = []
        arp_timeout = min(scan_timeout(scan_mode), 1.5)

        async for target in discover_targets(network, self.interface, arp_timeout):
            targets.append(target)
            yield DeviceFound(device=build_profile(target, []))

        limit = min(self.concurrency, scan_concurrency(scan_mode))
        semaphore = asyncio.Semaphore(limit)

        async def enrich(target: Target) -> DeviceProfile:
            async with semaphore:
                return await self._identify_target(target, scan_mode)

        tasks = [asyncio.create_task(enrich(target)) for target in targets]
        for task in asyncio.as_completed(tasks):
            device = await task
            self.cache.set(device.ip, device)
            yield DeviceUpdated(device=device)
            yield DeviceIdentified(device=device)

        duration = time.monotonic() - started
        checked = max(0, ipaddress.ip_network(network).num_addresses - 2)
        summary = ScanSummary(
            duration=duration,
            targets_checked=checked,
            devices_found=len(targets),
            mode=scan_mode.value,
        )
        yield ScanCompleted(summary=summary)

    async def watch_network(
        self,
        subnet: str | None = None,
        *,
        mode: ScanMode | str = ScanMode.PASSIVE,
        interval: float = 2.0,
    ) -> AsyncIterator[ScanEvent]:
        """Watch the OS neighbor table without sending probes"""
        if parse_scan_mode(mode) is not ScanMode.PASSIVE:
            raise ValueError("watch_network only supports passive mode")

        network = self._network(subnet)
        seen: set[str] = set()

        while True:
            async for target in known_neighbors(network):
                key = target.mac or target.ip
                if key in seen:
                    continue

                seen.add(key)
                device = await self._identify_target(target, ScanMode.PASSIVE)
                yield DeviceFound(device=device)

            await asyncio.sleep(interval)

    def preview_cloud_payload(self, device: DeviceProfile) -> dict[str, str]:
        """Show the data that cloud enrichment would receive"""
        if self.fingerbank is None:
            return {}

        target = Target(ip=device.ip, mac=device.mac)
        return self.fingerbank.preview_payload(target, device.evidence)

    async def _identify_target(self, target: Target, mode: ScanMode) -> DeviceProfile:
        names = scan_collectors(mode)
        collectors = [self.collectors[name] for name in names if name in self.collectors]
        timeout = min(self.timeout, scan_timeout(mode))
        evidence = await collect_evidence(collectors, target, timeout)

        if mode in {ScanMode.NORMAL, ScanMode.DEEP, ScanMode.PASSIVE}:
            evidence.extend(apply_local_rules(evidence))

        if self.fingerbank and mode is not ScanMode.FAST:
            try:
                evidence.extend(await self.fingerbank.resolve(target, evidence))
            except Exception as error:
                logger.debug("Fingerbank enrichment failed: %s", error)

        return build_profile(target, evidence)

    async def _find_neighbor(self, ip: str) -> Target:
        subnet = str(ipaddress.ip_network(f"{ip}/32", strict=False))
        async for target in known_neighbors(subnet):
            return target
        return Target(ip=ip)

    def _network(self, subnet: str | None) -> str:
        return validate_subnet(subnet or local_subnet(self.interface))
