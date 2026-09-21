# Troubleshooting

## No devices are found

Start with the operating system neighbor table

```powershell
arp -a
```

On Linux, also try

```bash
ip neigh show
```

If the table contains devices but HostLens does not return them, confirm that the selected subnet includes those addresses

If the table is empty, try fast mode with the required raw packet permissions

On Windows, check that Npcap is installed

## The wrong subnet is scanned

VPN and virtual adapters can become the preferred route

Select the real LAN interface

```python
intel = HostLens(interface="Wi-Fi")
```

Or pass the subnet directly

```python
devices = await intel.scan_network("192.168.1.0/24")
```

## A device has only an IP address

That means discovery found the host but the enabled collectors did not produce stronger evidence

Try normal or deep mode, then inspect `device.evidence`

Some devices do not publish names or discovery services and cannot be identified reliably from the LAN

For the highest name coverage, use the DHCP lease data or API from the router, Pi-hole, or network controller

Those systems receive hostnames during address assignment, while an ordinary LAN client does not have access to the full lease table

## A scan looks stale

Host profiles are cached for five minutes on each `HostLens` instance

Clear the cache when testing changes on a device

```python
intel.cache.clear()
```

## A collector fails silently

Collector failures are isolated by design

Enable debug logging while diagnosing a protocol

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

Applications decide how logging is configured

The library never calls `logging.basicConfig()` itself

## The CLI command is missing

Check the active interpreter and installation

```bash
python -m pip show hostlens
python -m hostlens.cli --help
```

Activate the virtual environment if `python -m hostlens.cli` works but `hostlens` does not

## `asyncio.run()` raises an error

The synchronous `identify()` and `discover()` helpers use `asyncio.run()`

They should not be called from a running event loop such as an async web handler or notebook cell

Use `identify_async`, `discover_async`, or `HostLens` there

```python
from hostlens import identify_async

device = await identify_async("192.168.1.42")
```

## Fingerbank returns no enrichment

Fast mode does not make cloud requests

Use normal or deep mode and verify that the preview payload contains useful values

```python
print(intel.preview_cloud_payload(device))
```

Enable debug logging to see a request failure without exposing the API key
