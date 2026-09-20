# Architecture

HostLens separates device discovery from evidence collection and identity selection

```text
interface and subnet selection
            |
            v
neighbor table and ARP discovery
            |
            v
      Target(ip, mac)
            |
            v
concurrent evidence collectors
            |
            v
local rules and optional Fingerbank
            |
            v
deduplication and field selection
            |
            v
       DeviceProfile
```

## Dependency direction

Lower-level modules do not import the client or CLI

```text
models
  ^
  |
network, parsers
  ^
  |
collectors, identity
  ^
  |
client and module helpers
  ^
  |
CLI
```

This keeps parsers and fusion logic usable in unit tests without opening sockets

## Module map

`api.py`
: Synchronous and asynchronous convenience functions

`client.py`
: Public orchestration, caching, bounded host concurrency, and scan events

`config.py`
: Scan modes and their collector, timeout, and concurrency settings

`cache.py`
: Small process-local TTL cache

`models/`
: Public Pydantic models for targets, evidence, profiles, services, results, and events

`network/`
: Address normalization, interface selection, neighbor table parsing, and ARP discovery

`collectors/`
: Protocol I/O that returns evidence

`parsers/`
: Deterministic conversion from protocol bytes or packet values into normal Python values and evidence

`identity/`
: Local fingerprint rules, Fingerbank integration, evidence fusion, and confidence selection

`cli/`
: Typer commands and Rich terminal output

## One-host flow

`HostLens.scan_host` performs these steps

1. Normalize the supplied IP address
2. Return a cached profile when one is still valid
3. Look for the address in the operating system neighbor table
4. Select collectors from the scan mode
5. Run collectors together with one timeout per collector
6. Apply local rules for normal, deep, and passive identification
7. Query Fingerbank when it is configured and the mode allows it
8. Build the profile and store it in the cache

`scan_hosts` reuses `scan_host` and adds one semaphore for bounded concurrency

## Network scan flow

`scan_stream` determines the subnet, reads known neighbors, and performs one ARP discovery request

Targets are deduplicated by IP and MAC during discovery

The stream yields a baseline `DeviceFound` event for each target

Enrichment tasks then run under a shared semaphore

Each completed task yields `DeviceUpdated` and `DeviceIdentified`

The last event contains duration, address count, device count, and mode

`scan_network` consumes the same stream and keeps the latest profile for each MAC address or IP address

## Collector isolation

`collect_evidence` runs selected collectors with `asyncio.gather`

Each collector runs inside `asyncio.timeout`

An exception from one collector produces a debug log and an empty evidence list for that collector

This is why an mDNS or UPnP failure does not erase a valid hostname or manufacturer result

Cancellation still follows normal asyncio behavior because `CancelledError` is not an `Exception` in supported Python versions

## Evidence fusion

Fusion starts by removing evidence with the same source, field, and case-insensitive value

Only recognized profile fields take part in final field selection

The candidates are scored with their confidence and the reliability assigned to their source family

The winning value retains every supporting source

Its field confidence combines supporting evidence by reducing remaining uncertainty and is capped at `0.99`

Overall profile confidence is the average of selected field confidences

A target with only a MAC address gets a baseline confidence of `0.4`

A target with only an IP address gets `0.2`

These numbers are heuristics for ordering and display

## Local rules

Local rules consume evidence and return more evidence

They do not mutate a profile or bypass fusion

Current rules recognize Google Cast, AirPlay, IPP printers, HomeKit, UPnP media renderers, and a conservative Samsung device hint

Keeping rule output as evidence makes the final result explainable and lets stronger observations win

## Cloud boundary

The Fingerbank client accepts a `Target` and evidence list

It builds a small payload from supported values and parses the response into evidence

Raw response dictionaries do not leave that module

The public client only creates a Fingerbank client after explicit cloud configuration

## Cache boundary

The cache stores completed profiles by IP for five minutes

It is not global and is not shared between `HostLens` instances

There is no disk cache, database, background cleanup task, or external service
