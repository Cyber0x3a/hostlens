<div align="center">

# HostLens

### Find and understand devices on your local network from Python

[![Test and publish](https://github.com/Cyber0x3a/hostlens/actions/workflows/workflow.yml/badge.svg)](https://github.com/Cyber0x3a/hostlens/actions/workflows/workflow.yml)
[![PyPI](https://img.shields.io/pypi/v/hostlens?color=3775A9)](https://pypi.org/project/hostlens/)
[![Python](https://img.shields.io/pypi/pyversions/hostlens?color=FFD43B)](https://pypi.org/project/hostlens/)
[![License](https://img.shields.io/github/license/Cyber0x3a/hostlens)](LICENSE)

Simple public API · Async first · Explainable results · No cloud calls by default

</div>

HostLens discovers devices on a LAN, collects useful facts about them, and turns
those facts into one clean device profile

It uses ARP, the local neighbor table, reverse DNS, OUI data, mDNS, SSDP, UPnP,
NetBIOS, and a small set of useful service checks

The normal API stays small even though the scan can use several protocols behind
the scenes

## Install

```bash
pip install hostlens
```

HostLens supports Python 3.11 and newer on Windows, Linux, and macOS

For local development

```bash
git clone https://github.com/Cyber0x3a/hostlens.git
cd hostlens
python -m venv .venv
```

Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Linux and macOS

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Identify one device

```python
from hostlens import identify

device = identify("192.168.1.42")

print(device.best_name)
print(device.manufacturer)
print(device.device_type)
print(device.model)
print(device.os)
print(device.confidence)
```

Possible result

```text
Samsung QN90C
Samsung Electronics
smart_tv
QN90C
Tizen
0.94
```

Unknown values stay `None`

HostLens does not fill gaps with strings like `Unknown` or `N/A`

## Async API

Async is the main implementation and the sync helpers are only thin wrappers

```python
from hostlens import HostLens

intel = HostLens()
device = await intel.identify("192.168.1.42")
```

Scan one host deeply

```python
device = await intel.scan_host("192.168.1.42", mode="deep")
```

Scan several hosts with bounded concurrency

```python
devices = await intel.scan_hosts(
    [
        "192.168.1.20",
        "192.168.1.21",
        "192.168.1.30",
    ],
    mode="normal",
)
```

Scan a subnet

```python
devices = await intel.scan_network("192.168.1.0/24")
```

Let HostLens detect the local subnet

```python
devices = await intel.scan_network()
```

Pick an interface when the machine has more than one active connection

```python
intel = HostLens(interface="Wi-Fi")
devices = await intel.scan_network()
```

## Scan modes

| Mode | Good for | What it does |
| --- | --- | --- |
| `fast` | A quick inventory | Neighbor table, ARP, reverse DNS, and OUI |
| `normal` | Everyday use | Fast scan plus mDNS, SSDP, UPnP, and local rules |
| `deep` | More detail | Normal scan plus NetBIOS and selected TCP services |
| `passive` | Quiet observation | Reads devices already visible in the OS neighbor table |

Normal mode is the default

Deep mode checks a small curated set of useful ports rather than scanning every
port on every device

```python
from hostlens import HostLens, ScanMode

intel = HostLens(timeout=3, concurrency=64)
devices = await intel.scan_network(mode=ScanMode.FAST)
```

## Progressive results

Applications do not need to wait for every collector to finish

HostLens first reports the device and then sends enriched updates

```python
from hostlens.models import DeviceFound, DeviceUpdated, ScanCompleted

async for event in intel.scan_stream("192.168.1.0/24", mode="normal"):
    match event:
        case DeviceFound(device=device):
            print("found", device.ip)

        case DeviceUpdated(device=device):
            print("updated", device.best_name)

        case ScanCompleted(summary=summary):
            print(summary)
```

Ask for a full scan result when summary data matters

```python
result = await intel.scan_network(mode="fast", return_result=True)

print(result.summary.duration)
print(result.summary.targets_checked)
print(result.summary.devices_found)
```

## Device profile

Every scan returns the same public model

```python
device.ip
device.mac
device.hostname
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

Pydantic serialization is available without another conversion layer

```python
data = device.model_dump()
json_data = device.model_dump_json(indent=2)
```

## Evidence and confidence

HostLens keeps the raw facts that produced a profile

```python
for item in device.evidence:
    print(item.source, item.field, item.value, item.confidence)
```

You can also get a readable explanation

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

Confidence values are heuristic scores for ranking evidence

They are not presented as mathematically calibrated probabilities

## Privacy and Fingerbank

Local scanning works without an account or API key

Cloud enrichment is disabled by default and HostLens never sends device data to
Fingerbank unless the caller enables it

```python
intel = HostLens(
    cloud=True,
    fingerbank_api_key="your-api-key",
)
```

Preview the payload before any cloud lookup

```python
payload = intel.preview_cloud_payload(device)
print(payload)
```

API keys are not stored in evidence and are not written to logs

## CLI

The CLI calls the same Python API used by applications

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

## How the code is organized

```text
src/hostlens/
├── api.py              sync and async convenience functions
├── client.py           public orchestration API
├── config.py           scan mode defaults
├── models/             public Pydantic models and scan events
├── network/            addressing, neighbor table, and ARP discovery
├── collectors/         one focused module for each protocol
├── parsers/            deterministic protocol parsing
├── identity/           fingerprints, Fingerbank, and evidence fusion
└── cli/                commands and terminal output
```

The dependency flow stays simple

```text
network discovery
      ↓
evidence collectors
      ↓
local or cloud identity hints
      ↓
evidence fusion
      ↓
DeviceProfile
```

Collectors collect facts

Parsers parse protocol data

Fingerprint rules interpret facts

Fusion picks the final values

The client only coordinates those steps

## Platform notes

Active ARP discovery uses Scapy

Windows may need [Npcap](https://npcap.com/) and an elevated terminal for raw ARP
access

Linux may need root or the relevant raw socket capability

When raw ARP is unavailable, HostLens can still use the local neighbor table and
the collectors that work in the current environment

## Development

```bash
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pytest
python -m build
```

The normal unit test suite does not need a live network

Tests that use a real LAN should use the `network` marker

## Local benchmark

The benchmark runs three fast scans and prints only aggregate timing and counts

It never prints local IP addresses or MAC addresses

```bash
python benchmarks/local_scan.py
```

Fast scan performance depends on ARP access, the operating system neighbor table,
DNS response time, interface size, and the number of visible devices

## Publishing

The GitHub Actions workflow lives at `.github/workflows/workflow.yml`

Every push and pull request runs formatting, linting, typing, tests, and package
builds

Publishing uses PyPI trusted publishing when a version tag such as `v0.1.0` is pushed

The PyPI project needs a trusted publisher for

```text
Owner       Cyber0x3a
Repository  hostlens
Workflow    workflow.yml
```

## License

[MIT](LICENSE)
