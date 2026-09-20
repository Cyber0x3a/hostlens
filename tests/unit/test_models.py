from hostlens.models import DeviceProfile, Evidence


def test_best_name_and_explanation_use_real_evidence() -> None:
    evidence = Evidence(
        source="upnp",
        field="model",
        value="QN90C",
        confidence=0.98,
        description="UPnP modelName reports QN90C",
    )
    device = DeviceProfile(
        ip="192.168.1.42",
        manufacturer="Samsung",
        model="QN90C",
        confidence=0.94,
        evidence=[evidence],
    )

    assert device.best_name == "Samsung QN90C"
    assert "Confidence: 94%" in device.explain()
    assert "UPnP modelName reports QN90C" in device.explain()


def test_generated_hostname_falls_back_to_identity() -> None:
    device = DeviceProfile(
        ip="192.168.1.2",
        hostname="android-deadbeef",
        manufacturer="Google",
        device_type="phone",
    )

    assert device.best_name == "Google phone"
