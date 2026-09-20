from hostlens.identity.fingerbank import FingerbankClient
from hostlens.models import Evidence, Target


def test_fingerbank_payload_contains_only_supported_evidence() -> None:
    client = FingerbankClient("secret")
    target = Target(ip="192.168.1.2", mac="AA:BB:CC:DD:EE:FF")
    evidence = [
        Evidence(source="dhcp", field="hostname", value="phone", confidence=0.9),
        Evidence(source="upnp", field="serial_number", value="private", confidence=0.9),
    ]

    assert client.preview_payload(target, evidence) == {
        "mac": "AA:BB:CC:DD:EE:FF",
        "hostname": "phone",
    }


def test_fingerbank_response_is_typed_evidence() -> None:
    evidence = FingerbankClient("secret")._parse_device({"name": "Android Phone"})

    assert len(evidence) == 1
    assert evidence[0].field == "device_type"
    assert evidence[0].value == "Android Phone"
