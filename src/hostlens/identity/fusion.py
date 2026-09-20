"""Conservative evidence fusion"""

import json
from collections.abc import Iterable

from hostlens.models import DeviceProfile, Evidence, FieldValue, Service, Target

PROFILE_FIELDS = {"hostname", "friendly_name", "manufacturer", "device_type", "model", "os"}

SOURCE_RELIABILITY = {
    "upnp": 1.0,
    "fingerbank": 0.95,
    "mdns": 0.9,
    "netbios": 0.8,
    "hostname": 0.8,
    "oui": 0.75,
}


def build_profile(target: Target, evidence: Iterable[Evidence]) -> DeviceProfile:
    """Build one device profile from collected evidence"""
    unique_evidence = _deduplicate(evidence)
    fields = _select_fields(unique_evidence)

    confidence_values = [field.confidence for field in fields.values()]
    if confidence_values:
        confidence = sum(confidence_values) / len(confidence_values)
    elif target.mac:
        confidence = 0.4
    else:
        confidence = 0.2

    return DeviceProfile(
        ip=target.ip,
        mac=target.mac,
        hostname=_value(fields, "hostname"),
        friendly_name=_value(fields, "friendly_name"),
        manufacturer=_value(fields, "manufacturer"),
        device_type=_value(fields, "device_type"),
        model=_value(fields, "model"),
        os=_value(fields, "os"),
        services=_services_from_evidence(unique_evidence),
        confidence=min(confidence, 1.0),
        fields=fields,
        evidence=unique_evidence,
    )


def _value(fields: dict[str, FieldValue], name: str) -> str | None:
    field = fields.get(name)
    return field.value if field else None


def _select_fields(evidence: list[Evidence]) -> dict[str, FieldValue]:
    grouped: dict[str, list[Evidence]] = {}

    for item in evidence:
        if item.field not in PROFILE_FIELDS or not isinstance(item.value, str):
            continue
        grouped.setdefault(item.field, []).append(item)

    selected: dict[str, FieldValue] = {}
    for field, candidates in grouped.items():
        selected[field] = _select_best_value(candidates)

    return selected


def _select_best_value(candidates: list[Evidence]) -> FieldValue:
    scores: dict[str, float] = {}
    sources: dict[str, set[str]] = {}
    display_values: dict[str, str] = {}

    for item in candidates:
        if not isinstance(item.value, str):
            continue

        key = item.value.casefold().strip()
        source = item.source.split(":", 1)[0]
        reliability = SOURCE_RELIABILITY.get(source, 0.8)

        scores[key] = scores.get(key, 0.0) + item.confidence * reliability
        sources.setdefault(key, set()).add(item.source)
        display_values[key] = item.value.strip()

    winner = max(scores, key=lambda key: scores[key])
    confidence = _combined_confidence(candidates, winner)

    return FieldValue(
        value=display_values[winner],
        confidence=confidence,
        sources=tuple(sorted(sources[winner])),
    )


def _combined_confidence(candidates: list[Evidence], winner: str) -> float:
    remaining_uncertainty = 1.0

    for item in candidates:
        if not isinstance(item.value, str):
            continue
        if item.value.casefold().strip() == winner:
            remaining_uncertainty *= 1.0 - item.confidence

    return min(1.0 - remaining_uncertainty, 0.99)


def _deduplicate(evidence: Iterable[Evidence]) -> list[Evidence]:
    unique: list[Evidence] = []
    seen: set[tuple[str, str, str]] = set()

    for item in evidence:
        key = (item.source, item.field, str(item.value).casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique


def _services_from_evidence(evidence: list[Evidence]) -> list[Service]:
    services: dict[tuple[str, int | None], Service] = {}

    for item in evidence:
        if item.field == "service" and isinstance(item.value, str):
            service = Service(name=item.value, service_type=item.value)
            services[(service.name, service.port)] = service

        if item.field != "services" or not isinstance(item.value, list):
            continue

        for raw_service in item.value:
            try:
                service = Service.model_validate(json.loads(raw_service))
            except (ValueError, TypeError):
                continue
            services[(service.name, service.port)] = service

    return list(services.values())
