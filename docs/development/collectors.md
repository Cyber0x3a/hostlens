# Collectors and parsers

A collector performs network or system I/O and returns evidence

A parser accepts data it was given and does not perform I/O

Keep that boundary visible when adding protocol support

## Collector contract

The shared protocol is intentionally small

```python
class Collector(Protocol):
    name: str

    async def collect(
        self,
        target: Target,
        timeout: float,
    ) -> list[Evidence]: ...
```

The name must match a collector name listed for at least one scan mode before the built-in client will select it

## Built-in collectors

| Name | Module | Work performed |
| --- | --- | --- |
| `hostname` | `collectors/basic.py` | Reverse DNS lookup |
| `oui` | `collectors/basic.py` | Local MAC manufacturer lookup |
| `mdns` | `collectors/mdns.py` | Browse selected mDNS service types |
| `ssdp` | `collectors/ssdp.py` | Send a unicast SSDP search to one target |
| `upnp` | `collectors/upnp.py` | Find and fetch target-owned UPnP descriptions |
| `netbios` | `collectors/netbios.py` | Query a NetBIOS name in deep mode |
| `services` | `collectors/services.py` | Connect to a short list of TCP ports in deep mode |

## Adding a collector

1. Put protocol I/O in a focused module under `collectors/`
2. Return `Evidence` for facts the target actually reported
3. Put byte, header, XML, or packet parsing in `parsers/` when it can be tested separately
4. Export the collector from `collectors/__init__.py`
5. Add it to `_built_in_collectors()` in `client.py`
6. Add its name to the intended modes in `config.py`
7. Add unit tests for parsing, timeout behavior, malformed input, and useful output
8. Update the scanning and API documentation

Do not make a collector choose the final manufacturer, type, model, or operating system when it only has a hint

Return the hint as evidence and let fusion decide

## Timeout behavior

The shared runner wraps every collector in `asyncio.timeout`

A collector should still pass the timeout to blocking calls, socket timeouts, and HTTP clients so its own resources stop promptly

Use `asyncio.to_thread` for a blocking library call that has no asynchronous API

Do not catch cancellation

Catch narrow protocol errors inside the collector only when a partial result can still be returned

## Evidence fields

Final profile selection currently recognizes these string fields

```text
hostname
friendly_name
manufacturer
device_type
model
os
```

Other fields remain useful as raw evidence and can drive local rules

Current examples include `server`, `upnp_location`, `device_type_raw`, `model_number`, `serial_number`, `dhcp_fingerprint`, and `dhcp_vendor`

Use stable snake_case names

## Confidence

A collector confidence describes the strength of one observation

It must be between 0 and 1

Use higher confidence for explicit metadata returned by the device and lower confidence for indirect inference

Source reliability weights used during conflicts live in `identity/fusion.py`

Do not add another hidden weighting table to a collector

## Descriptions

Add a short evidence description when the raw field and value do not explain themselves well

```python
Evidence(
    source="upnp",
    field="model",
    value="QN90C",
    confidence=0.95,
    description="UPnP modelName reports QN90C",
)
```

`DeviceProfile.explain()` uses this text directly

Never put credentials, authorization headers, or private request data in a description or metadata mapping

## Parser rules

Parsers should accept deterministic input and return an empty result for malformed data when malformed packets are expected on the network

They should not open sockets, read environment variables, configure logging, or depend on a `HostLens` instance

The existing parsers cover DHCP option tuples, SSDP headers, and UPnP description XML

## Custom collectors in application code

Applications can replace the built-in list

```python
from hostlens import HostLens
from hostlens.models import Evidence, Target


class InventoryCollector:
    name = "inventory"

    async def collect(self, target: Target, timeout: float) -> list[Evidence]:
        return []


intel = HostLens(collectors=[InventoryCollector()])
```

This constructor argument replaces the built-ins

If an application wants both, it must pass both its collector and the built-in collector instances it needs
