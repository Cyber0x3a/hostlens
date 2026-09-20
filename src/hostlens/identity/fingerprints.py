"""Readable local fingerprint rules"""

from hostlens.models import Evidence


def apply_local_rules(evidence: list[Evidence]) -> list[Evidence]:
    """Add conservative identity hints for facts we recognize"""
    derived: list[Evidence] = []

    if _contains(evidence, "service", "_googlecast"):
        derived.extend(
            _result("chromecast", 0.9, manufacturer="Google", device_type="media_player")
        )

    if _contains(evidence, "service", "_airplay"):
        derived.extend(_result("airplay", 0.82, device_type="media_player"))

    if _contains(evidence, "service", "_ipp"):
        derived.extend(_result("printer", 0.94, device_type="printer"))

    if _contains(evidence, "service", "_hap"):
        derived.extend(_result("homekit", 0.84, device_type="smart_home"))

    if _contains(evidence, "device_type_raw", "mediarenderer"):
        derived.extend(_result("upnp-renderer", 0.9, device_type="media_player"))

    if _contains(evidence, "manufacturer", "samsung"):
        derived.extend(_result("samsung-tv", 0.78, device_type="smart_tv"))

    return derived


def _contains(evidence: list[Evidence], field: str, text: str) -> bool:
    return any(item.field == field and text in str(item.value).lower() for item in evidence)


def _result(rule: str, confidence: float, **fields: str) -> list[Evidence]:
    evidence: list[Evidence] = []

    for field, value in fields.items():
        evidence.append(
            Evidence(
                source=f"local:{rule}",
                field=field,
                value=value,
                confidence=confidence,
                description=f"Local rule {rule} matched collected evidence",
            )
        )

    return evidence
