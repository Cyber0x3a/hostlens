# Testing

Ordinary tests must not depend on a live network

Protocol input should be supplied as bytes, model values, or monkeypatched function results

## Run the suite

```bash
python -m pytest
```

Run with the same coverage command used in CI

```bash
python -m pytest --cov=hostlens --cov-report=term-missing
```

Run one file or one test while working

```bash
python -m pytest tests/unit/test_fusion.py
python -m pytest tests/unit/test_cli.py::test_cli_rejects_conflicting_profiles
```

## Test layout

`test_parsers.py`
: Deterministic DHCP, SSDP, and UPnP parsing

`test_networking.py`
: Address normalization and neighbor table parsing

`test_models.py`
: Best-name selection and evidence explanations

`test_fusion.py`
: Deduplication, supporting evidence, conflicts, and local rules

`test_fingerbank.py`
: Payload filtering and response parsing

`test_client.py`
: Collector failure isolation and host concurrency

`test_config_cache.py`
: Scan mode validation and TTL cache behavior

`test_cli.py`
: Command arguments and terminal-independent error text

## Async tests

The project uses `pytest-asyncio` with automatic mode enabled

```python
async def test_example() -> None:
    result = await some_async_function()
    assert result
```

Existing explicit `pytest.mark.asyncio` markers are also valid

## Mock network boundaries

Patch the narrow function that performs I/O

Examples include `_read_neighbor_table`, `_scan_arp`, `query_ssdp`, `socket.gethostbyaddr`, and an `httpx` client boundary

Do not make a unit test depend on the developer's router, DNS server, neighbor cache, or privileges

Custom collectors are a simple way to test orchestration

```python
class FixedCollector:
    name = "hostname"

    async def collect(self, target, timeout):
        return [
            Evidence(
                source="hostname",
                field="hostname",
                value="test-device",
                confidence=0.8,
            )
        ]
```

## Live network tests

Tests that intentionally use a LAN must use the `network` marker

```python
import pytest


@pytest.mark.network
async def test_local_scan() -> None: ...
```

Keep those tests out of the default CI path unless the runner has an explicit test network

The benchmark in `benchmarks/local_scan.py` is a manual live-network check, not a unit test

It prints timing and counts without printing device addresses

## CLI output tests

Rich may add ANSI codes and line wrapping depending on the terminal

Normalize styled output before asserting error text

Prefer testing the user-visible message and exit code over a complete terminal snapshot

## Before opening a pull request

```bash
python -m ruff format --check .
python -m ruff check .
python -m pyright
python -m pytest
python -m build
python -m mkdocs build --strict
```

Run the full list after changing package metadata, public imports, workflows, or documentation navigation
