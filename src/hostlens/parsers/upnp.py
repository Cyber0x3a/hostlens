"""UPnP XML parsing"""

from xml.etree import ElementTree

from hostlens.models import Evidence

FIELDS = {
    "friendlyName": "friendly_name",
    "manufacturer": "manufacturer",
    "modelName": "model",
    "modelNumber": "model_number",
    "modelDescription": "model_description",
    "deviceType": "device_type_raw",
    "serialNumber": "serial_number",
    "UDN": "device_id",
}


def parse_upnp_description(data: bytes) -> list[Evidence]:
    """Turn a UPnP device description into normalized evidence"""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        return []

    evidence: list[Evidence] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        field = FIELDS.get(tag)
        value = (element.text or "").strip()
        if not field or not value:
            continue

        evidence.append(
            Evidence(
                source="upnp",
                field=field,
                value=value,
                confidence=0.95,
                description=f"UPnP {tag} reports {value}",
            )
        )

    return evidence
