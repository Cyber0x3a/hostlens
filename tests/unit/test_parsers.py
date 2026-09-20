from hostlens.parsers import parse_dhcp_options, parse_ssdp_headers, parse_upnp_description


def test_ssdp_headers_are_case_insensitive() -> None:
    data = b"HTTP/1.1 200 OK\r\nLOCATION: http://192.0.2.2/root.xml\r\nServer: Linux\r\n\r\n"

    headers = parse_ssdp_headers(data)

    assert headers == {"location": "http://192.0.2.2/root.xml", "server": "Linux"}


def test_upnp_xml_is_normalized() -> None:
    xml = b"""<?xml version='1.0'?>
    <root xmlns='urn:schemas-upnp-org:device-1-0'><device>
      <friendlyName>Living Room TV</friendlyName>
      <manufacturer>Samsung</manufacturer><modelName>QN90C</modelName>
    </device></root>"""

    evidence = parse_upnp_description(xml)

    assert {(item.field, item.value) for item in evidence} == {
        ("friendly_name", "Living Room TV"),
        ("manufacturer", "Samsung"),
        ("model", "QN90C"),
    }


def test_malformed_upnp_xml_is_ignored() -> None:
    assert parse_upnp_description(b"<broken") == []


def test_dhcp_options_form_stable_fingerprint() -> None:
    evidence = parse_dhcp_options(
        [("hostname", b"phone"), ("vendor_class_id", b"android"), ("param_req_list", [1, 3, 6])]
    )

    assert [(item.field, item.value) for item in evidence] == [
        ("hostname", "phone"),
        ("dhcp_vendor", "android"),
        ("dhcp_fingerprint", "1,3,6"),
    ]
