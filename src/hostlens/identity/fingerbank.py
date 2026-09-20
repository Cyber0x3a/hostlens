"""Asynchronous Fingerbank resolver"""

from __future__ import annotations

import httpx

from hostlens.exceptions import CloudResolverError
from hostlens.models import Evidence, Target


class FingerbankClient:
    """Resolve normalized device evidence through the opt-in Fingerbank API"""

    endpoint = "https://api.fingerbank.org/api/v2/combinations/interrogate"

    def __init__(self, api_key: str, timeout: float = 5.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def preview_payload(self, target: Target, evidence: list[Evidence]) -> dict[str, str]:
        payload: dict[str, str] = {}
        if target.mac:
            payload["mac"] = target.mac
        for item in evidence:
            if item.field == "hostname" and isinstance(item.value, str):
                payload["hostname"] = item.value
            elif item.field == "dhcp_fingerprint" and isinstance(item.value, str):
                payload["dhcp_fingerprint"] = item.value
            elif item.field == "dhcp_vendor" and isinstance(item.value, str):
                payload["dhcp_vendor"] = item.value
        return payload

    async def resolve(self, target: Target, evidence: list[Evidence]) -> list[Evidence]:
        payload = self.preview_payload(target, evidence)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.endpoint, params={"key": self.api_key, **payload})
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise CloudResolverError(f"Fingerbank request failed: {error}") from error
        device = data.get("device") or {}
        return self._parse_device(device)

    def _parse_device(self, device: object) -> list[Evidence]:
        if not isinstance(device, dict):
            return []
        mapping = {"name": "device_type", "parent_name": "device_type"}
        result: list[Evidence] = []
        for remote_field, local_field in mapping.items():
            value = device.get(remote_field)
            if isinstance(value, str) and value:
                result.append(
                    Evidence(
                        source="fingerbank",
                        field=local_field,
                        value=value,
                        confidence=0.85,
                        description=f"Fingerbank identifies the device as {value}",
                    )
                )
                break
        return result
