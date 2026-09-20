"""Convenient module-level sync and async APIs"""

from __future__ import annotations

import asyncio

from hostlens.client import HostLens
from hostlens.models import DeviceProfile


async def identify_async(target: str) -> DeviceProfile:
    """Identify one network device asynchronously"""
    return await HostLens().identify(target)


def identify(target: str) -> DeviceProfile:
    """Identify one network device from synchronous code"""
    return asyncio.run(identify_async(target))


async def discover_async(subnet: str | None = None) -> list[DeviceProfile]:
    """Discover devices on a subnet asynchronously"""
    return await HostLens().discover(subnet)


def discover(subnet: str | None = None) -> list[DeviceProfile]:
    """Discover devices on a subnet from synchronous code"""
    return asyncio.run(discover_async(subnet))
