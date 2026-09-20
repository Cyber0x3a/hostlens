from hostlens.identity.fingerprints import apply_local_rules
from hostlens.identity.fusion import build_profile
from hostlens.models import Evidence, Target


def test_fusion_deduplicates_and_combines_support() -> None:
    evidence = [
        Evidence(source="oui", field="manufacturer", value="Samsung", confidence=0.78),
        Evidence(source="upnp", field="manufacturer", value="Samsung", confidence=0.95),
        Evidence(source="oui", field="manufacturer", value="Samsung", confidence=0.78),
        Evidence(source="mdns", field="manufacturer", value="Other", confidence=0.4),
    ]

    device = build_profile(Target(ip="192.168.1.4"), evidence)

    assert device.manufacturer == "Samsung"
    assert device.fields["manufacturer"].sources == ("oui", "upnp")
    assert len(device.evidence) == 3
    assert device.fields["manufacturer"].confidence > 0.98


def test_local_fingerprint_rule_uses_observed_service() -> None:
    evidence = [
        Evidence(
            source="mdns",
            field="service",
            value="_googlecast._tcp.local.",
            confidence=0.9,
        )
    ]

    derived = apply_local_rules(evidence)

    assert {(item.field, item.value) for item in derived} == {
        ("manufacturer", "Google"),
        ("device_type", "media_player"),
    }
