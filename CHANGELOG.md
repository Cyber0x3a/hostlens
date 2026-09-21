# Changelog

## 0.2.0 - 2026-09-21

- Added reverse mDNS and LLMNR hostname lookups to normal scans
- Added NetBIOS hostname lookup to normal scans and replaced fixed-offset parsing
- Changed mDNS to enumerate advertised DNS-SD service types once per scan
- Changed SSDP and UPnP to use one multicast discovery pass per scan
- Added friendly name, model, and manufacturer evidence from mDNS service data
- Added friendly names to CLI device output
- Ignored network and broadcast addresses found in operating system neighbor tables

## 0.1.1 - 2026-09-20

- Fixed positional subnet arguments for the `scan`, `discover`, and `watch` CLI commands
- Added the full documentation site and refreshed the README

## 0.1.0 - 2026-09-20

- First public API for host identification and subnet scanning
- Fast, normal, deep, and passive profiles
- Neighbor-table and ARP discovery with progressive events
- Reverse DNS, OUI, mDNS, SSDP, UPnP, NetBIOS, and selected service collectors
- Explainable evidence fusion and opt-in Fingerbank enrichment
- Typer and Rich CLI
- Clean feature folders for models, network code, collectors, parsers, identity, and CLI
- PyPI trusted publishing workflow
