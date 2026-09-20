"""Network target model"""

from pydantic import BaseModel, ConfigDict


class Target(BaseModel):
    """One host found during discovery"""

    model_config = ConfigDict(frozen=True)

    ip: str
    mac: str | None = None
    interface: str | None = None
