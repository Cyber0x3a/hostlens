"""Progressive scan event models"""

from typing import Literal

from pydantic import BaseModel, Field

from hostlens.models.device import DeviceProfile


class ScanSummary(BaseModel):
    duration: float = Field(ge=0)
    targets_checked: int = Field(ge=0)
    devices_found: int = Field(ge=0)
    mode: str


class ScanResult(BaseModel):
    devices: list[DeviceProfile]
    summary: ScanSummary


class DeviceFound(BaseModel):
    type: Literal["device_found"] = "device_found"
    device: DeviceProfile


class DeviceUpdated(BaseModel):
    type: Literal["device_updated"] = "device_updated"
    device: DeviceProfile


class DeviceIdentified(BaseModel):
    type: Literal["device_identified"] = "device_identified"
    device: DeviceProfile


class ScanCompleted(BaseModel):
    type: Literal["scan_completed"] = "scan_completed"
    summary: ScanSummary


ScanEvent = DeviceFound | DeviceUpdated | DeviceIdentified | ScanCompleted
