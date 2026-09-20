# First scan

Use a network you own or have permission to inspect

## Start with fast mode

Fast mode gives a useful first result with the least traffic

```python
import asyncio

from hostlens import HostLens


async def main() -> None:
    intel = HostLens()
    devices = await intel.scan_network(mode="fast")

    for device in devices:
        print(f"{device.ip:15} {device.best_name}")


asyncio.run(main())
```

Save the example as `scan.py` and run it outside the repository checkout

```bash
python scan.py
```

## Scan a known subnet

Pass the network in CIDR notation

```python
devices = await intel.scan_network("192.168.1.0/24", mode="normal")
```

HostLens refuses ranges larger than 65,536 addresses

Active subnet discovery currently supports IPv4

## Select an interface

Automatic detection uses the preferred local IPv4 route

On a machine with several active adapters, select the interface by its system name or friendly name

```python
intel = HostLens(interface="Wi-Fi")
devices = await intel.scan_network()
```

An unknown interface raises `InterfaceNotFound`

## Identify one address

```python
device = await intel.scan_host("192.168.1.42", mode="deep")
print(device.explain())
```

`scan_host` validates the address, checks the neighbor table for its MAC address, runs the collectors selected by the mode, and builds a profile

## Get scan metadata

The common return value is a list of devices

Ask for a `ScanResult` when duration and counts matter

```python
from hostlens.models import ScanResult

result = await intel.scan_network(mode="fast", return_result=True)

if isinstance(result, ScanResult):
    print(result.summary.duration)
    print(result.summary.targets_checked)
    print(result.summary.devices_found)
```

## Stream results

Streaming lets a UI or long-running process show an address before enrichment finishes

```python
from hostlens.models import DeviceFound, DeviceUpdated, ScanCompleted

async for event in intel.scan_stream(mode="normal"):
    if isinstance(event, DeviceFound):
        print("found", event.device.ip)
    elif isinstance(event, DeviceUpdated):
        print("updated", event.device.best_name)
    elif isinstance(event, ScanCompleted):
        print("done", event.summary.duration)
```

See [scanning modes](scanning.md) for the work each mode performs
