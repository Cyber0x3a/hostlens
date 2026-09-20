<div align="center">

# HostLens

Find devices on a local network and turn what they expose into readable Python objects

[Documentation](https://cyber0x3a.github.io/hostlens/) &nbsp;·&nbsp;
[PyPI](https://pypi.org/project/hostlens/) &nbsp;·&nbsp;
[Examples](examples/) &nbsp;·&nbsp;
[Contributing](CONTRIBUTING.md)

[![Test and publish](https://github.com/Cyber0x3a/hostlens/actions/workflows/workflow.yml/badge.svg?branch=main)](https://github.com/Cyber0x3a/hostlens/actions/workflows/workflow.yml)
[![PyPI version](https://img.shields.io/pypi/v/hostlens.svg?style=flat-square&logo=pypi&logoColor=white&cacheSeconds=300)](https://pypi.org/project/hostlens/)
[![Python versions](https://img.shields.io/pypi/pyversions/hostlens.svg?style=flat-square&logo=python&logoColor=white&cacheSeconds=300)](https://pypi.org/project/hostlens/)
[![License](https://img.shields.io/pypi/l/hostlens.svg?style=flat-square&cacheSeconds=300)](LICENSE)

</div>

```bash
pip install hostlens
```

```python
from hostlens import identify

device = identify("192.168.1.42")

print(device.best_name)
print(device.manufacturer)
print(device.device_type)
print(device.confidence)
```

```text
Samsung QN90C
Samsung Electronics
smart_tv
0.94
```

HostLens uses the local neighbor table, ARP, reverse DNS, OUI data, mDNS, SSDP, UPnP, NetBIOS, and a short list of useful TCP services

Unknown values stay `None`

Cloud enrichment stays off unless the caller enables it

## Why HostLens exists

Most LAN discovery code stops at an IP and MAC address or exposes protocol-specific dictionaries

HostLens gives callers one `DeviceProfile` with the evidence that produced it

| What you need | What HostLens gives you |
| --- | --- |
| Quick inventory | Neighbor table and ARP discovery with fast enrichment |
| A useful name | Friendly name, hostname, model, or manufacturer fallback |
| Explainable identity | Raw evidence, selected fields, sources, and confidence |
| Async application support | Async client, bounded concurrency, and streaming events |
| A script or shell command | Sync helpers and the `hostlens` CLI |
| Local-only operation | No account, API key, or cloud request by default |

## Scan a network

Async is the main implementation

```python
import asyncio

from hostlens import HostLens


async def main() -> None:
    intel = HostLens()
    devices = await intel.scan_network(mode="normal")

    for device in devices:
        print(f"{device.ip:15} {device.best_name}")


asyncio.run(main())
```

HostLens detects the preferred local IPv4 subnet when one is not supplied

Pass a CIDR range when you want an exact network

```python
devices = await intel.scan_network("192.168.1.0/24", mode="fast")
```

Select an interface on machines with several active adapters

```python
intel = HostLens(interface="Wi-Fi")
```

## Scanning modes

| Mode | Use it for | Collectors |
| --- | --- | --- |
| `fast` | Quick inventory | Neighbor table, ARP, reverse DNS, OUI |
| `normal` | Everyday identification | Fast mode, mDNS, SSDP, UPnP, local rules |
| `deep` | More evidence from one device or a small network | Normal mode, NetBIOS, selected TCP services |
| `passive` | Watching devices already known to the OS | Neighbor table and OUI without HostLens probes |

Normal mode is the default

Deep mode checks ports 22, 80, 443, 445, 554, and 9100

It does not perform an unrestricted port scan

[Read the scanning guide](https://cyber0x3a.github.io/hostlens/scanning/)

## Progressive results

A network scan can report a target before its enrichment collectors finish

```python
from hostlens.models import DeviceFound, DeviceUpdated, ScanCompleted

async for event in intel.scan_stream("192.168.1.0/24", mode="normal"):
    if isinstance(event, DeviceFound):
        print("found", event.device.ip)
    elif isinstance(event, DeviceUpdated):
        print("updated", event.device.best_name)
    elif isinstance(event, ScanCompleted):
        print("done", event.summary.duration)
```

Ask for counts and duration without using the event stream

```python
result = await intel.scan_network(mode="fast", return_result=True)

print(result.summary.targets_checked)
print(result.summary.devices_found)
print(result.summary.duration)
```

## Device profiles

Every scanning path returns the same Pydantic model

```python
device.ip
device.mac
device.hostname
device.friendly_name
device.manufacturer
device.device_type
device.model
device.os
device.services
device.confidence
device.fields
device.evidence
device.best_name
```

Serialize it without another conversion layer

```python
data = device.model_dump()
json_data = device.model_dump_json(indent=2)
```

Inspect the facts behind a result

```python
for item in device.evidence:
    print(item.source, item.field, item.value, item.confidence)
```

Or print the built-in explanation

```python
print(device.explain())
```

```text
Samsung QN90C
Confidence: 94%

Evidence:
- MAC prefix matches Samsung Electronics
- UPnP manufacturer reports Samsung Electronics
- UPnP modelName reports QN90C
- mDNS advertises _airplay._tcp.local
```

Confidence values are heuristics for choosing and ranking evidence

They are not calibrated probabilities

[Read about profiles and evidence](https://cyber0x3a.github.io/hostlens/device-profiles/)

## Command line

The CLI calls the same Python API

```bash
hostlens identify 192.168.1.20
hostlens identify 192.168.1.20 --deep

hostlens scan
hostlens scan --fast
hostlens scan --deep
hostlens scan 192.168.1.0/24

hostlens discover
hostlens watch --passive
```

[Read the CLI guide](https://cyber0x3a.github.io/hostlens/cli/)

## Privacy and Fingerbank

Local scanning works without an account or API key

Fingerbank is opt in

```python
import os

intel = HostLens(
    cloud=True,
    fingerbank_api_key=os.environ["FINGERBANK_API_KEY"],
)
```

Preview the values that would leave the machine

```python
payload = intel.preview_cloud_payload(device)
print(payload)
```

API keys are not added to evidence or logs

[Read the cloud and privacy guide](https://cyber0x3a.github.io/hostlens/cloud/)

## Platform notes

HostLens supports Python 3.11 and newer on Windows, Linux, and macOS

Active ARP discovery may need extra system access

<details>
<summary><strong>Windows</strong></summary>

Install [Npcap](https://npcap.com/) when Scapy cannot open the network adapter

Some systems also need an elevated terminal

</details>

<details>
<summary><strong>Linux</strong></summary>

The process needs raw socket access for active ARP discovery

The neighbor table can still work without it

</details>

<details>
<summary><strong>macOS</strong></summary>

Raw packet access may require elevation

The neighbor table and application-level collectors can still return results

</details>

[Read all platform notes](https://cyber0x3a.github.io/hostlens/platforms/)

## Documentation

| Start here | Developer material |
| --- | --- |
| [Installation](https://cyber0x3a.github.io/hostlens/installation/) | [Development setup](https://cyber0x3a.github.io/hostlens/development/setup/) |
| [First scan](https://cyber0x3a.github.io/hostlens/first-scan/) | [Architecture](https://cyber0x3a.github.io/hostlens/development/architecture/) |
| [Python API](https://cyber0x3a.github.io/hostlens/api/) | [Collectors and parsers](https://cyber0x3a.github.io/hostlens/development/collectors/) |
| [Troubleshooting](https://cyber0x3a.github.io/hostlens/troubleshooting/) | [Testing](https://cyber0x3a.github.io/hostlens/development/testing/) |

Full documentation lives at [cyber0x3a.github.io/hostlens](https://cyber0x3a.github.io/hostlens/)

## Development

```bash
git clone https://github.com/Cyber0x3a/hostlens.git
cd hostlens
python -m venv .venv
python -m pip install -e ".[dev,docs]"

python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pytest
python -m build
python -m mkdocs build --strict
```

Normal unit tests do not use a live network

Live network tests must use the `network` marker

See [CONTRIBUTING.md](CONTRIBUTING.md) before changing protocol behavior or public models

## License

HostLens is available under the [MIT License](LICENSE)
