"""SSDP response parsing"""


def parse_ssdp_headers(data: bytes) -> dict[str, str]:
    """Parse case-insensitive HTTP-style headers from an SSDP message"""
    headers: dict[str, str] = {}

    for line in data.decode("utf-8", errors="replace").splitlines()[1:]:
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    return headers
