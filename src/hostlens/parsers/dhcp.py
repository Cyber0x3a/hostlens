"""Deterministic packet and protocol parsers"""

from __future__ import annotations

from collections.abc import Iterable

from hostlens.models import Evidence


def parse_dhcp_options(options: Iterable[tuple[str, object] | str]) -> list[Evidence]:
    """Normalize the useful fields from Scapy-style DHCP options"""
    values: dict[str, object] = {}
    for option in options:
        if isinstance(option, tuple) and len(option) == 2:
            values[option[0]] = option[1]

    evidence: list[Evidence] = []
    hostname = _text(values.get("hostname"))
    if hostname:
        evidence.append(Evidence(source="dhcp", field="hostname", value=hostname, confidence=0.9))

    vendor = _text(values.get("vendor_class_id"))
    if vendor:
        evidence.append(Evidence(source="dhcp", field="dhcp_vendor", value=vendor, confidence=0.85))

    requested = values.get("param_req_list")
    if isinstance(requested, (list, tuple)):
        fingerprint = ",".join(str(value) for value in requested)
        evidence.append(
            Evidence(
                source="dhcp",
                field="dhcp_fingerprint",
                value=fingerprint,
                confidence=0.9,
            )
        )
    return evidence


def _text(value: object) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip() or None
    if isinstance(value, str):
        return value.strip() or None
    return None
