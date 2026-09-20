"""Evidence and service models"""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
EvidenceValue = str | int | float | bool | list[str]


class Evidence(BaseModel):
    """One traceable fact or interpretation about a device"""

    model_config = ConfigDict(frozen=True)

    source: str
    field: str
    value: EvidenceValue
    confidence: Confidence
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    description: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class Service(BaseModel):
    """One network service advertised or observed on a device"""

    model_config = ConfigDict(frozen=True)

    name: str
    protocol: Literal["tcp", "udp"] | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    service_type: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class FieldValue(BaseModel):
    """A selected field value with its confidence and sources"""

    model_config = ConfigDict(frozen=True)

    value: str
    confidence: Confidence
    sources: tuple[str, ...]
