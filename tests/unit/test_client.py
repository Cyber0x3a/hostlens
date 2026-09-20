import asyncio

import pytest

from hostlens import HostLens
from hostlens.models import Evidence, Target


class WorkingCollector:
    name = "hostname"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        del target, timeout
        return [Evidence(source=self.name, field="hostname", value="living-room", confidence=0.8)]


class BrokenCollector:
    name = "oui"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        del target, timeout
        raise RuntimeError("collector failed")


@pytest.mark.asyncio
async def test_collector_failures_do_not_fail_identification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intel = HostLens(collectors=[WorkingCollector(), BrokenCollector()])

    async def unchanged(ip: str) -> Target:
        return Target(ip=ip)

    monkeypatch.setattr(intel, "_find_neighbor", unchanged)
    device = await intel.scan_host("192.168.1.20", mode="fast")

    assert device.hostname == "living-room"
    assert device.manufacturer is None


@pytest.mark.asyncio
async def test_scan_hosts_is_bounded_and_keeps_order(monkeypatch: pytest.MonkeyPatch) -> None:
    intel = HostLens(concurrency=2, collectors=[])
    active = 0
    maximum = 0

    async def identify(target: str, *, mode: object) -> object:
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return target

    monkeypatch.setattr(intel, "scan_host", identify)
    result = await intel.scan_hosts(["192.0.2.1", "192.0.2.2", "192.0.2.3"])

    assert result == ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
    assert maximum == 2
