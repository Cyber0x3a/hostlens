"""The public device profile"""

from pydantic import BaseModel, Field, computed_field

from hostlens.models.evidence import Confidence, Evidence, FieldValue, Service


class DeviceProfile(BaseModel):
    """A normalized and explainable identity for one network device"""

    ip: str
    mac: str | None = None
    hostname: str | None = None
    friendly_name: str | None = None
    manufacturer: str | None = None
    device_type: str | None = None
    model: str | None = None
    os: str | None = None
    services: list[Service] = Field(default_factory=list)
    confidence: Confidence = 0.0
    fields: dict[str, FieldValue] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def best_name(self) -> str:
        """Return the most useful observed name"""
        if self.friendly_name:
            return self.friendly_name
        if self.hostname and not _looks_generated(self.hostname):
            return self.hostname.rstrip(".")
        if self.manufacturer and self.model:
            return f"{self.manufacturer} {self.model}"
        if self.model:
            return self.model
        if self.manufacturer and self.device_type:
            readable_type = self.device_type.replace("_", " ")
            return f"{self.manufacturer} {readable_type}"
        if self.hostname:
            return self.hostname
        if self.ip:
            return self.ip
        if self.mac:
            return self.mac
        return "Device"

    def explain(self) -> str:
        """Explain the profile using only collected evidence"""
        lines = [self.best_name, f"Confidence: {self.confidence:.0%}"]

        if self.evidence:
            lines.extend(("", "Evidence:"))

        for item in self.evidence:
            detail = item.description
            if not detail:
                detail = f"{item.source} reports {item.field}={item.value}"
            lines.append(f"- {detail}")

        return "\n".join(lines)


def _looks_generated(hostname: str) -> bool:
    normalized = hostname.rstrip(".").lower()
    prefixes = ("android-", "desktop-", "dhcp-", "unknown-")
    return normalized.startswith(prefixes)
