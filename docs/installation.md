# Installation

## From PyPI

Create a virtual environment, activate it, then install HostLens

=== "Windows PowerShell"

    ```powershell
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install hostlens
    ```

=== "Linux and macOS"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install hostlens
    ```

Check the installed command

```bash
hostlens --help
```

## Python support

The package requires Python 3.11 or newer

The release workflow tests Python 3.11, 3.12, and 3.13

## Raw ARP access

HostLens first reads the operating system neighbor table, so it can still return known devices when raw ARP is unavailable

Active ARP discovery has platform requirements

### Windows

Install [Npcap](https://npcap.com/) when Scapy cannot open a network adapter

Some systems also require an elevated PowerShell or terminal

### Linux

Run from an account with raw socket access

For local testing, using `sudo` is the quickest check

For a service installation, grant only the capability the process needs instead of running the whole service as root

### macOS

Raw packet access can require elevated privileges

The neighbor table, reverse DNS, and application-level collectors can still work without it

## Development install

Clone the repository and install the development tools in editable mode

```bash
git clone https://github.com/Cyber0x3a/hostlens.git
cd hostlens
python -m venv .venv
python -m pip install -e ".[dev]"
```

The [developer setup](development/setup.md) page covers the checks used by the repository
