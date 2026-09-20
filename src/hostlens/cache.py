"""Small in-memory TTL cache"""

import time
from typing import Generic, TypeVar

T = TypeVar("T")


class MemoryCache(Generic[T]):
    def __init__(self, ttl: float = 300.0) -> None:
        self.ttl = ttl
        self.entries: dict[str, tuple[T, float]] = {}

    def get(self, key: str) -> T | None:
        entry = self.entries.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if expires_at <= time.monotonic():
            del self.entries[key]
            return None

        return value

    def set(self, key: str, value: T) -> None:
        self.entries[key] = (value, time.monotonic() + self.ttl)

    def clear(self) -> None:
        self.entries.clear()
