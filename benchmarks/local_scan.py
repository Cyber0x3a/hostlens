"""Measure a fast scan without printing device addresses"""

import asyncio
import json
import statistics
import time

from hostlens import HostLens
from hostlens.models import ScanResult


async def main() -> None:
    runs = []
    last_result: ScanResult | None = None

    for _ in range(3):
        started = time.perf_counter()
        result = await HostLens().scan_network(mode="fast", return_result=True)
        elapsed = time.perf_counter() - started

        if not isinstance(result, ScanResult):
            raise RuntimeError("Expected a scan result")

        runs.append(round(elapsed, 3))
        last_result = result

    if last_result is None:
        raise RuntimeError("Benchmark did not run")

    print(
        json.dumps(
            {
                "runs_seconds": runs,
                "median_seconds": round(statistics.median(runs), 3),
                "targets_checked": last_result.summary.targets_checked,
                "devices_found": last_result.summary.devices_found,
                "mode": last_result.summary.mode,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
