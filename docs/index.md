# HostLens

HostLens finds devices on a local network and turns the facts it observes into one device profile

It can read the operating system neighbor table, send an ARP discovery request, look up hostnames and manufacturers, inspect local discovery protocols, and check a short list of useful services

Nothing is sent to a cloud service unless Fingerbank is enabled by the caller

## Install

```bash
pip install hostlens
```

HostLens supports Python 3.11 and newer

## Identify one device

```python
from hostlens import identify

device = identify("192.168.1.42")

print(device.best_name)
print(device.manufacturer)
print(device.device_type)
print(device.confidence)
```

The synchronous helpers work well in scripts

Applications that already use `asyncio` should use `HostLens` or the async helper functions

```python
from hostlens import HostLens

intel = HostLens()
device = await intel.identify("192.168.1.42")
```

## Scan the local network

```python
devices = await intel.scan_network(mode="normal")

for device in devices:
    print(device.ip, device.best_name)
```

When no subnet is supplied, HostLens selects the preferred local IPv4 interface and uses its subnet

You can pass a CIDR range when automatic detection is not what you want

```python
devices = await intel.scan_network("192.168.1.0/24", mode="fast")
```

## Where to go next

- [Install HostLens and prepare the operating system](installation.md)
- [Run the first scan](first-scan.md)
- [Choose a scanning mode](scanning.md)
- [Read the Python API reference](api.md)
- [Set up a development checkout](development/setup.md)

## What HostLens does not do

HostLens is not a vulnerability scanner and it does not perform unrestricted port scans

Results depend on what a device exposes, what the operating system already knows, and whether the current process can send raw ARP requests

An unidentified field stays `None` rather than being guessed
