import pytest

from hostlens.network.addressing import normalize_mac, validate_subnet
from hostlens.network.discovery import parse_neighbor_table


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("aa-bb-cc-dd-ee-ff", "AA:BB:CC:DD:EE:FF"),
        ("aabb.ccdd.eeff", "AA:BB:CC:DD:EE:FF"),
        ("AA:BB:CC:DD:EE:FF", "AA:BB:CC:DD:EE:FF"),
    ],
)
def test_normalize_mac(raw: str, expected: str) -> None:
    assert normalize_mac(raw) == expected


def test_invalid_mac_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_mac("not-a-mac")


def test_neighbor_parser_handles_windows_and_linux() -> None:
    output = """
      192.168.1.10          aa-bb-cc-dd-ee-ff     dynamic
    192.168.1.11 dev eth0 lladdr 11:22:33:44:55:66 REACHABLE
    """

    targets = parse_neighbor_table(output)

    assert [(item.ip, item.mac) for item in targets] == [
        ("192.168.1.10", "AA:BB:CC:DD:EE:FF"),
        ("192.168.1.11", "11:22:33:44:55:66"),
    ]


def test_large_subnet_is_rejected() -> None:
    with pytest.raises(Exception, match="65,536"):
        validate_subnet("10.0.0.0/8")


def test_ipv6_active_scan_is_rejected() -> None:
    with pytest.raises(Exception, match="IPv4"):
        validate_subnet("2001:db8::/120")
