"""Terminal output for the HostLens CLI"""

from rich.console import Console
from rich.table import Table

from hostlens.models import DeviceProfile

console = Console()


def show_device(device: DeviceProfile) -> None:
    table = Table(title=device.best_name, show_header=False, box=None)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = (
        ("IP", device.ip),
        ("MAC", device.mac),
        ("Hostname", device.hostname),
        ("Friendly name", device.friendly_name),
        ("Manufacturer", device.manufacturer),
        ("Type", device.device_type),
        ("Model", device.model),
        ("OS", device.os),
        ("Confidence", f"{device.confidence:.0%}"),
    )

    for label, value in rows:
        if value is not None:
            table.add_row(label, str(value))

    console.print(table)


def show_found(ip: str) -> None:
    console.print(f"Found {ip}")


def show_summary(devices_found: int, duration: float) -> None:
    console.print(f"Found {devices_found} devices in {duration:.2f}s")
