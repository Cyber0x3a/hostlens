"""HostLens command-line interface"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Annotated

import typer

from hostlens.cli.output import show_device, show_found, show_summary
from hostlens.client import HostLens
from hostlens.config import ScanMode
from hostlens.models import DeviceFound, DeviceIdentified, ScanCompleted

app = typer.Typer(no_args_is_help=True, help="Discover and identify devices on a local network")


def _mode(fast: bool, deep: bool) -> ScanMode:
    if fast and deep:
        raise typer.BadParameter("Choose either --fast or --deep")
    if fast:
        return ScanMode.FAST
    if deep:
        return ScanMode.DEEP
    return ScanMode.NORMAL


@app.command()
def identify(
    target: str,
    deep: Annotated[bool, typer.Option("--deep", help="Use deeper service probes")] = False,
) -> None:
    """Identify one device"""
    device = asyncio.run(
        HostLens().scan_host(target, mode=ScanMode.DEEP if deep else ScanMode.NORMAL)
    )
    show_device(device)


@app.command()
def scan(
    subnet: Annotated[
        str | None,
        typer.Argument(help="IPv4 subnet in CIDR notation"),
    ] = None,
    fast: Annotated[bool, typer.Option("--fast", help="Favor discovery speed")] = False,
    deep: Annotated[bool, typer.Option("--deep", help="Use deeper service probes")] = False,
) -> None:
    """Discover and identify a local subnet"""

    async def run() -> None:
        async for event in HostLens().scan_stream(subnet, mode=_mode(fast, deep)):
            if isinstance(event, DeviceFound):
                show_found(event.device.ip)
            elif isinstance(event, DeviceIdentified):
                show_device(event.device)
            elif isinstance(event, ScanCompleted):
                show_summary(event.summary.devices_found, event.summary.duration)

    asyncio.run(run())


@app.command()
def discover(
    subnet: Annotated[
        str | None,
        typer.Argument(help="IPv4 subnet in CIDR notation"),
    ] = None,
) -> None:
    """Run a fast discovery scan"""
    devices = asyncio.run(HostLens().discover(subnet))
    for device in devices:
        show_device(device)


@app.command()
def watch(
    subnet: Annotated[
        str | None,
        typer.Argument(help="IPv4 subnet in CIDR notation"),
    ] = None,
    passive: Annotated[bool, typer.Option("--passive", help="Do not probe devices")] = True,
) -> None:
    """Watch for devices observed by the operating system"""
    if not passive:
        raise typer.BadParameter("watch currently supports passive observation only")

    async def run() -> None:
        async for event in HostLens().watch_network(subnet):
            if isinstance(event, DeviceFound):
                show_device(event.device)

    with suppress(KeyboardInterrupt):
        asyncio.run(run())


if __name__ == "__main__":
    app()
