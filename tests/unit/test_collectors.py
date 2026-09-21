from scapy.layers.dns import DNS, DNSQR, DNSRR
from scapy.layers.netbios import (
    NBNSHeader,
    NBNSNodeStatusResponse,
    NBNSNodeStatusResponseService,
)

from hostlens.collectors.local_names import hostname_from_ptr_response
from hostlens.collectors.mdns import service_evidence
from hostlens.collectors.netbios import hostname_from_response
from hostlens.config import ScanMode, scan_collectors


def test_normal_scan_uses_local_name_protocols() -> None:
    collectors = scan_collectors(ScanMode.NORMAL)

    assert "mdns" in collectors
    assert "netbios" in collectors
    assert "llmnr" in collectors


def test_dns_ptr_response_returns_hostname() -> None:
    response = DNS(
        id=123,
        qr=1,
        qd=DNSQR(qname="20.1.168.192.in-addr.arpa", qtype="PTR"),
        an=DNSRR(
            rrname="20.1.168.192.in-addr.arpa",
            type="PTR",
            rdata="DESKTOP.local",
        ),
    )

    assert hostname_from_ptr_response(bytes(response), 123) == "DESKTOP.local"
    assert hostname_from_ptr_response(bytes(response), 999) is None


def test_netbios_response_returns_workstation_name() -> None:
    workstation = NBNSNodeStatusResponseService(
        NETBIOS_NAME=b"DESKTOP        ",
        SUFFIX=0,
        NAME_FLAGS=4,
    )
    response = NBNSHeader(RESPONSE=1, ANCOUNT=1) / NBNSNodeStatusResponse(
        RR_NAME=b"*",
        NUM_NAMES=1,
        NODE_NAME=[workstation],
        MAC_ADDRESS="00:11:22:33:44:55",
    )

    assert hostname_from_response(bytes(response)) == "DESKTOP"


def test_mdns_service_exposes_names_and_model() -> None:
    evidence = service_evidence(
        "_googlecast._tcp.local.",
        "Living Room._googlecast._tcp.local.",
        "chromecast.local.",
        {b"fn": b"Living Room TV", b"md": b"Chromecast Ultra"},
    )

    values = {(item.field, item.value) for item in evidence}
    assert ("hostname", "chromecast.local") in values
    assert ("friendly_name", "Living Room TV") in values
    assert ("model", "Chromecast Ultra") in values
