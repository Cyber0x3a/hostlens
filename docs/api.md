# API reference

The top-level package keeps common imports short

```python
from hostlens import (
    DeviceProfile,
    HostLens,
    ScanMode,
    discover,
    discover_async,
    identify,
    identify_async,
)
```

Models, scan events, collectors, parsers, and exceptions remain available from their own modules

## HostLens

```python
HostLens(
    *,
    interface: str | None = None,
    timeout: float = 3.0,
    concurrency: int = 64,
    cloud: bool = False,
    fingerbank_api_key: str | None = None,
    collectors: Sequence[Collector] | None = None,
)
```

### Constructor arguments

`interface`
: System adapter name or friendly name used for automatic subnet detection and ARP discovery

`timeout`
: Maximum collector timeout in seconds, must be greater than zero

`concurrency`
: Maximum number of hosts enriched at once, must be at least one

`cloud`
: Enables Fingerbank enrichment when true

`fingerbank_api_key`
: Fingerbank key required when cloud enrichment is enabled

`collectors`
: Optional sequence replacing all built-in collectors, mainly useful for tests and custom integrations

Each instance owns its configuration, collectors, Fingerbank client, and in-memory profile cache

### identify

```python
await intel.identify(
    target: str,
    *,
    mode: ScanMode | str = ScanMode.NORMAL,
) -> DeviceProfile
```

Alias for `scan_host` with the same behavior

### scan_host

```python
await intel.scan_host(
    target: str,
    *,
    mode: ScanMode | str = ScanMode.NORMAL,
) -> DeviceProfile
```

Validates one address, checks the cache, looks for its MAC in the neighbor table, collects evidence, and returns a profile

### scan_hosts

```python
await intel.scan_hosts(
    targets: Sequence[str],
    *,
    mode: ScanMode | str = ScanMode.NORMAL,
) -> list[DeviceProfile]
```

Scans several addresses with bounded concurrency

The returned list follows the input order

### scan_network

```python
await intel.scan_network(
    subnet: str | None = None,
    *,
    mode: ScanMode | str = ScanMode.NORMAL,
    return_result: bool = False,
) -> list[DeviceProfile] | ScanResult
```

Discovers devices and enriches them

If `subnet` is absent, the local subnet is detected from the preferred or selected interface

The common return value is a device list

Set `return_result=True` to receive a `ScanResult` with a `ScanSummary`

### discover

```python
await intel.discover(subnet: str | None = None) -> list[DeviceProfile]
```

Runs `scan_network` in fast mode

### scan

```python
intel.scan(subnet: str | None = None) -> AsyncIterator[ScanEvent]
```

Streams a normal scan

This is the short form of `scan_stream(subnet, mode="normal")`

### scan_stream

```python
intel.scan_stream(
    subnet: str | None = None,
    *,
    mode: ScanMode | str = ScanMode.NORMAL,
) -> AsyncIterator[ScanEvent]
```

Yields `DeviceFound` for initial discovery, followed by `DeviceUpdated` and `DeviceIdentified` after enrichment

The final event is `ScanCompleted`

Passive mode is rejected here because it has no natural completion point

### watch_network

```python
intel.watch_network(
    subnet: str | None = None,
    *,
    mode: ScanMode | str = ScanMode.PASSIVE,
    interval: float = 2.0,
) -> AsyncIterator[ScanEvent]
```

Reads the neighbor table repeatedly and yields each newly observed device once

The iterator runs until it is cancelled or closed

Only passive mode is accepted

### preview_cloud_payload

```python
intel.preview_cloud_payload(device: DeviceProfile) -> dict[str, str]
```

Returns the values that the configured Fingerbank client would receive

Returns an empty dictionary when cloud enrichment is disabled

## Module-level helpers

### identify

```python
identify(target: str) -> DeviceProfile
```

Synchronous helper that creates a default client and calls `asyncio.run()`

### identify_async

```python
await identify_async(target: str) -> DeviceProfile
```

Async helper that creates a default client and identifies one address

### discover

```python
discover(subnet: str | None = None) -> list[DeviceProfile]
```

Synchronous fast discovery helper

### discover_async

```python
await discover_async(subnet: str | None = None) -> list[DeviceProfile]
```

Async fast discovery helper

## ScanMode

`ScanMode` is a string enum

```python
from hostlens import ScanMode

ScanMode.FAST
ScanMode.NORMAL
ScanMode.DEEP
ScanMode.PASSIVE
```

Methods also accept the lowercase strings `fast`, `normal`, `deep`, and `passive`

Unknown values raise `ConfigurationError`

## Models

Import public models from `hostlens.models`

### DeviceProfile

See [device profiles](device-profiles.md) for field details, evidence, confidence, and serialization

### Evidence

```python
Evidence(
    source: str,
    field: str,
    value: str | int | float | bool | list[str],
    confidence: float,
    observed_at: datetime,
    description: str | None = None,
    metadata: dict[str, str] = {},
)
```

Confidence is validated from 0 through 1

Evidence models are frozen after construction

### FieldValue

```python
FieldValue(
    value: str,
    confidence: float,
    sources: tuple[str, ...],
)
```

Records the selected value and the evidence sources that supported it

### Service

```python
Service(
    name: str,
    protocol: Literal["tcp", "udp"] | None = None,
    port: int | None = None,
    service_type: str | None = None,
    metadata: dict[str, str] = {},
)
```

Ports are validated from 1 through 65535

### Target

```python
Target(
    ip: str,
    mac: str | None = None,
    interface: str | None = None,
)
```

Internal collectors receive a `Target`

It is public so custom collectors can use the same input model

### ScanSummary and ScanResult

```python
ScanSummary(
    duration: float,
    targets_checked: int,
    devices_found: int,
    mode: str,
)

ScanResult(
    devices: list[DeviceProfile],
    summary: ScanSummary,
)
```

## Events

All events are Pydantic models with a literal `type` field

| Event | Type value | Payload |
| --- | --- | --- |
| `DeviceFound` | `device_found` | Baseline device profile |
| `DeviceUpdated` | `device_updated` | Enriched device profile |
| `DeviceIdentified` | `device_identified` | Completed identity for one target |
| `ScanCompleted` | `scan_completed` | Scan summary |

`ScanEvent` is the union of these four models

## Exceptions

Import exceptions from `hostlens.exceptions`

```text
HostLensError
├── ConfigurationError
├── DiscoveryError
│   ├── PermissionDenied
│   └── InterfaceNotFound
├── TargetUnreachable
├── CollectorError
└── ResolverError
    └── CloudResolverError
```

`ConfigurationError`
: Invalid timeout, concurrency, mode, or cloud configuration

`DiscoveryError`
: Invalid subnet or failure to determine the local interface or subnet

`InterfaceNotFound`
: Selected interface is missing or has no usable IPv4 address

`CloudResolverError`
: Direct Fingerbank client request failed

Individual collector failures are normally isolated and returned as missing evidence rather than raised through `HostLens`

## Custom collectors

A collector needs a name and one async method

```python
from hostlens.models import Evidence, Target


class CameraCollector:
    name = "camera"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        return []
```

Pass the complete collector list to the client

```python
intel = HostLens(collectors=[CameraCollector()])
```

Supplying `collectors` replaces the built-in list rather than extending it

See [collectors and parsers](development/collectors.md) before adding a collector to the project
